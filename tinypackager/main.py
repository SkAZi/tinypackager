import click, os
import yaml as yaml_lib
from create import PackageCreate
from update import PackageUpdate
from freeze import PackageFreeze
from utils import read_yaml_exit, deepmerge
from __init__ import __version__

# TODO: remove folders if empty
# TODO: local packages storage


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
@click.option('--access_key', envvar='S3_ACCESS_KEY', default=None, help='Access key.')
@click.option('--secret_key', envvar='S3_SECRET_KEY', default=None, help='Secret key.')
@click.option('--bump_version', '-b', is_flag=True, help='Auto increment version number.')
@click.option('--file', '-f',  is_flag=True, help='Read list of packages from file.')
def create(packages, root, bucket, access_key, secret_key, bump_version, file):
    show_version()
    backpwd = os.getcwd()

    if not file:
        pwd = os.getcwd()
        if len(packages) == 0: packages = ('package.yml',)
        for package in packages:
            folder, file = os.path.split(package)
            os.chdir(folder)
            PackageCreate(root, file, bucket=bucket, access_key=access_key, 
                secret_key=secret_key, bump_version=bump_version, dest_path=pwd)
            os.chdir(pwd)

    else:
        for package_list in packages:
            folder, file = os.path.split(package_list)
            os.chdir(folder)
            pwd = os.getcwd()
            for package in read_yaml_exit(file).get('create', []):
                folder, file = os.path.split(package)
                os.chdir(folder)
                PackageCreate(root, file, bucket=bucket, access_key=access_key, 
                    secret_key=secret_key, bump_version=bump_version, dest_path=backpwd)
                os.chdir(pwd)
    

    os.chdir(backpwd)

@cli.command()
@click.argument('flags', nargs=-1)
@click.option('--root', '-r', default="root.yml", help='Root file name.')
@click.option('--bucket', envvar='TINYLIMA_BUCKET', default="tinylima-assets", help='AWS bucket name.')
@click.option('--access_key', envvar='S3_ACCESS_KEY', default=None, help='Access key.')
@click.option('--secret_key', envvar='S3_SECRET_KEY', default=None, help='Secret key.')
def update(flags, root, bucket, access_key, secret_key):
    show_version()
    args = {}
    for s in flags:
        try:
            key, value = s.split('=')
            args[str(key)] = str(value)
        except:
            print "Warning: flag %s can not be parsed" % s

    folder, file = os.path.split(root)
    pwd = os.getcwd()
    os.chdir(folder)
    PackageUpdate(file, args, bucket, access_key, secret_key)
    os.chdir(pwd)

@cli.command()
@click.option('--root', '-r', default="root.yml", help='Root file name.')
def freeze(root):
    show_version()
    folder, file = os.path.split(root)
    pwd = os.getcwd()
    os.chdir(folder)
    PackageFreeze(file)
    os.chdir(pwd)


@cli.command()
@click.argument('yamls', nargs=-1)
def yaml(yamls):
    if len(yamls) == 0: exit(1)

    data = read_yaml_exit(yamls[0])
    for fyaml in yamls[1:]:
        append = read_yaml_exit(fyaml)
        data = deepmerge(data, append)

    print yaml_lib.dump(data, default_flow_style=False, allow_unicode=True)


if __name__ == '__main__':
    cli()
    