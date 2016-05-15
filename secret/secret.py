#!/usr/bin/env python
from __future__ import absolute_import
from __future__ import print_function
import logging, os, sys
from pprint import pprint as pp

from secret.project import get_project
from secret.cli import prepare

def trollius_log(level=logging.CRITICAL):
    os.environ['TROLLIUSDEBUG'] = "1" # more informative tracebacks
    logging.basicConfig(level=level)

if sys.version_info.major == 2:
    trollius_log()

from secret.storage import S3
from secret.output import prettyprint

import boto3

import trollius as asyncio
from trollius import From, Return

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
    storage = S3(session=session,
            vault=args.vault,
            vaultkey=args.vaultkey,
            env=args.env,
            region=args.region,
            prefix=args.project,
            project=project,)

    method = getattr(storage, args.action)
    fn = lambda: method(**vars(args))
    result = yield From(fn())
    prettyprint(result, args)

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
