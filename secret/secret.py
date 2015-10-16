#!/usr/bin/env python
from __future__ import absolute_import
import logging, os, sys
from pprint import pprint as pp

from secret.project import get_project
from secret.cli import prepare

def trollius_log(level=logging.CRITICAL):
    os.environ['TROLLIUSDEBUG'] = "1" # more informative tracebacks
    logging.basicConfig(level=level)

if sys.version_info.major == 2:
    trollius_log()

if __name__ == '__main__':
    """ Basic actions before imports for a responsive CLI """
    prepare()

from secret.storage import S3

import boto3
import six
import trollius as asyncio
from trollius import From, Return
from tabulate import tabulate

def prettyprint(result):
    def is_str(result):
        try:
            return isinstance(result, basestring)
        except NameError:
            return isinstance(result, str)
    if any(isinstance(result, k) for k in [list]):
        print("Keys:")
        for k in result:
            print(k)
    elif is_str(result):
        print(result)
    else:
        table = [["Key", "Value"]]
        for k,v in six.iteritems(result):
            table.append([k,v])
        print(tabulate(table, numalign='left', tablefmt='plain'))

@asyncio.coroutine
def main(args):
    project = get_project(args.datafile)
    
    region = os.getenv("AWS_DEFAULT_REGION", args.region)
    kw = {}
    if not os.getenv("AWS_PROFILE"):
        kw = dict(aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            aws_session_token=os.getenv('AWS_SESSION_TOKEN'),)

    if args.debug:
        boto3.set_stream_logger(name='botocore')
        trollius_log(level=logging.DEBUG)

    session = boto3.session.Session(region_name=region, **kw)
    storage = S3(session=session, vault=args.vault, vaultkey=args.vaultkey, env=args.env, project=project)

    method = getattr(storage, args.action)
    result = yield From(method(**vars(args)))
    prettyprint(result)

def runner():
    args = prepare()
    loop = asyncio.get_event_loop()
    # wrap asyncio to suppress stacktraces
    if args.debug:
        loop.run_until_complete(main(args))
    else:
        try:
            loop.run_until_complete(main(args))
        except Exception as e:
            print(e.message)
    loop.close()

if __name__ == '__main__':
    runner()
