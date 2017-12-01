import click
import yaml
import os
from create import PackageCreate
from update import PackageUpdate
from freeze import PackageFreeze

@click.group()
def cli():
    pass

@cli.command()
@click.argument('packages', nargs=-1)
@click.option('--root', default="root.yml", help='Package name')
@click.option('--bucket', envvar='TINYLIMA_BUCKET', default="tinylima-assets", help='Bucket')
@click.option('--access_key', envvar='ACCESS_KEY', default=None, help='Access key')
@click.option('--secret_key', envvar='SECRET_KEY', default=None, help='Secret key')
@click.option('--bump_version', is_flag=True, help='Bump version')
def create(packages, root, bucket, access_key, secret_key, bump_version):
    if len(packages) == 0: packages = ('package.yml',)
    for package in packages:
        PackageCreate(root, package, bucket=bucket, access_key=access_key, 
            secret_key=secret_key, bump_version=bump_version)

@cli.command()
@click.argument('flags', nargs=-1)
@click.option('--root', default="root.yml", help='Package name')
@click.option('--bucket', envvar='TINYLIMA_BUCKET', default="tinylima-assets", help='Bucket')
@click.option('--access_key', envvar='ACCESS_KEY', default=None, help='Access key')
@click.option('--secret_key', envvar='SECRET_KEY', default=None, help='Secret key')
def update(flags, root, bucket, access_key, secret_key):
    args = {}
    for s in flags:
        try:
            key, value = s.split('=')
            args[str(key)] = str(value)
        except:
            print "Warning: flag %s can not be parsed" % s

    PackageUpdate(root, args, bucket, access_key, secret_key)

@cli.command()
@click.option('--root', default="root.yml", help='Package name')
def freeze(root):
    PackageFreeze(root)


if __name__ == '__main__':
    cli()
    