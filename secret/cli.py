from __future__ import absolute_import

import argparse, sys, os
from secret.project import get_project
from secret.templates import statusT, helpT

DATAFILE = '.secret'
ALIASES = {'ls':'list',}

def print_status(args):
    aws_profile = bool(os.getenv("AWS_PROFILE"))
    aws_key = bool(os.getenv('AWS_ACCESS_KEY_ID'))
    aws_secret = bool(os.getenv('AWS_SECRET_ACCESS_KEY'))
    print(statusT.format(args.vault, args.vaultkey, args.project, args.env, aws_profile, aws_key, aws_secret))

def prepare():
    p = argparse.ArgumentParser()
    p.add_argument("action", help="list,get,put,envs,config,setup")
    p.add_argument("key", nargs="?", default=None)
    p.add_argument("value", nargs="?", default=None)
    p.add_argument("--version", default=None)
    p.add_argument("--region", help="AWS region", default="us-east-1")
    p.add_argument("--vaultkey", help="Name of KMS key", default="alias/secret")
    p.add_argument("--vault", help="Name of vault (eg. S3 bucket)", default="secret")
    p.add_argument("--project", help="Name of project (eg. S3 'folder')", default=None)
    p.add_argument("--env", help="Environment namespace for keys", default='default')
    p.add_argument("--datafile", default=DATAFILE)
    p.add_argument("--debug", default=None)
    if len(sys.argv) == 1:
        sys.exit(p.print_help())
    args = p.parse_args()
    args.action = ALIASES.get(args.action, args.action)

    project = get_project(args.datafile)

    if args.action not in ['setup']:
        args.vault = project.load().get('vault', args.vault)
        args.project = project.load().get('project', args.project)
        args.vaultkey = project.load().get('key', args.vaultkey)
        args.region = project.load().get('region', args.region)
        if not all([args.vault, args.project]):
            sys.exit("Vault and/or Project configuration undefined")

    if args.action == 'help':
        print_status(args)
        sys.exit(helpT)

    return args
