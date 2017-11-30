#!/usr/bin/env python

from setuptools import setup

setup(
    name='tinypackager',
    version='0.3',
    packages=['tinypackager'],
    include_package_data=True,
    install_requires=[
        'Click', 'PyYAML', 'boto'
    ],
    entry_points={
        'console_scripts': [
            'tinypackager = tinypackager.main:cli'
        ]
    },
)