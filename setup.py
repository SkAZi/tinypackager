#!/usr/bin/env python

from setuptools import setup
from tinypackager.main import __version__

setup(
    name='tinypackager',
    version=__version__,
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