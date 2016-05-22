from __future__ import absolute_import

try:# PY2
    import ConfigParser as configparser
except:
    import configparser
import argparse, sys, os
from secret.project import get_project
from secret.templates import statusT, helpT

DATAFILE = '.secret'
ALIASES = {'ls':'list','rm':'delete'}

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
    p.add_argument("--region", help="AWS region of KMS and S3", default=None)
    p.add_argument("--vaultkey", help="Name of KMS key", default=None)
    p.add_argument("--vault", help="Name of vault (eg. S3 bucket)", default=None)
    p.add_argument("-P", "--project", help="Name of project (eg. S3 'folder')", default=None)
    p.add_argument("--env", help="Environment namespace for keys", default='default')
    p.add_argument("-F","--fmt", help="Output format", default='console')
    p.add_argument("-o","--output", help="Output to console (default) or given filepath", default='')
    p.add_argument("--datafile", default=DATAFILE)
    p.add_argument("--debug", default=None)
    if len(sys.argv) == 1:
        sys.exit(p.print_help())
    args = p.parse_args()
    args.action = ALIASES.get(args.action, args.action)

    project = get_project(args.datafile)

    # Arguments preference: CLI -> .secret -> globals

    args.project = args.project if (args.project is not None) else project.load().get('project', '')
    args.vault = args.vault or project.load().get('vault')
    args.vaultkey = args.vaultkey or project.load().get('key')
    args.region = args.region or project.load().get('region')

    secret_profile = os.getenv("SECRET_PROFILE", "default")
    config = configparser.SafeConfigParser()
    config.read(os.path.expanduser('~/.secret/credentials'))
    if config.has_section(secret_profile):
        if not args.vault:
            args.vault = config.get(secret_profile, 'vault', raw=0)
        if not args.vaultkey:
            args.vaultkey = config.get(secret_profile, 'vaultkey', raw=0)
        if not args.region:
            args.region = config.get(secret_profile, 'region', raw=0)

    if not all([args.vault]):
        sys.exit("Vault configuration undefined: --vault, --vaultkey")

    if args.action == 'help':
        print_status(args)
        sys.exit(helpT)

    return args
