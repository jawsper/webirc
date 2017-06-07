#!/usr/bin/env python3

from setuptools import setup, find_packages

import sys
sys.path.insert(0, 'src')
from webirc import __version__

setup(
    name='webirc',
    version=__version__,
    author='Jasper Seidel',
    author_email='code@jawsper.nl',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    url='https://github.com/jawsper/webirc',
    license='LICENSE',
    description='Web-based IRC client.',
    long_description=open('README.rst').read(),
    install_requires=[
    ],
    classifiers=[
        'Development Status :: 1 - Planning',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
    ],

    test_suite='tests',
)