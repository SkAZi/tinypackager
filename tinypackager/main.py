import click, yaml, os
from create import PackageCreate
from update import PackageUpdate
from freeze import PackageFreeze
from utils import read_yaml_exit

__version__ = '0.3.4'

def show_version():
    print "tinypackager v.%s" % __version__

@click.group()
@click.version_option(__version__)
def cli():
    pass

@cli.command()
@click.argument('packages', nargs=-1)
@click.option('--root', '-r', default="root.yml", help='Root file name.')
@click.option('--bucket', envvar='TINYLIMA_BUCKET', default="tinylima-assets", help='AWS bucket name.')
@click.option('--access_key', envvar='ACCESS_KEY', default=None, help='Access key.')
@click.option('--secret_key', envvar='SECRET_KEY', default=None, help='Secret key.')
@click.option('--bump_version', '-b', is_flag=True, help='Auto increment version number.')
@click.option('--file', '-f',  is_flag=True, help='Read list of packages from file.')
def create(packages, root, bucket, access_key, secret_key, bump_version, file):
    show_version()
    pwd = os.getcwd()
    if file:
        ret = []
        for package in packages:
            ret.extend(read_yaml_exit(package).get('create', []))
        packages = ret
    
    if len(packages) == 0: packages = ('package.yml',)

    for package in packages:
        folder, file = os.path.split(package)
        os.chdir(folder)
        PackageCreate(root, file, bucket=bucket, access_key=access_key, 
            secret_key=secret_key, bump_version=bump_version, dest_path=pwd)
        os.chdir(pwd)

@cli.command()
@click.argument('flags', nargs=-1)
@click.option('--root', '-r', default="root.yml", help='Root file name.')
@click.option('--bucket', envvar='TINYLIMA_BUCKET', default="tinylima-assets", help='AWS bucket name.')
@click.option('--access_key', envvar='ACCESS_KEY', default=None, help='Access key.')
@click.option('--secret_key', envvar='SECRET_KEY', default=None, help='Secret key.')
def update(flags, root, bucket, access_key, secret_key):
    show_version()
    args = {}
    for s in flags:
        try:
            key, value = s.split('=')
            args[str(key)] = str(value)
        except:
            print "Warning: flag %s can not be parsed" % s

    PackageUpdate(root, args, bucket, access_key, secret_key)

@cli.command()
@click.option('--root', '-r', default="root.yml", help='Root file name.')
def freeze(root):
    show_version()
    PackageFreeze(root)


if __name__ == '__main__':
    cli()
    