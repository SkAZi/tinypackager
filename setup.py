#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='tinypackager',
    version='0.2',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Click', 'PyYAML', 'boto'
    ],
    entry_points='''
        [console_scripts]
        tinypackager=tinypackager.main:cli
    ''',
)