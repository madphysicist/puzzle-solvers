#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# puzzle-solvers: a library of tools for solving puzzles
#
# Copyright (C) 2019  Joseph R. Fox-Rabinovitz <jfoxrabinovitz at gmail dot com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# Author: Joseph Fox-Rabinovitz <jfoxrabinovitz at gmail dot com>
# Version: 28 May 2019: Initial Coding


"""
Setup script for building and installing Puzzle Solvers.
"""

from os.path import dirname, join
import sys

from setuptools import setup


DIST_NAME = 'puzzle-solvers'

LICENSE = 'MIT'
DESCRIPTION = 'Program for creating MS Word reports from data and content templates'

AUTHOR = 'Joseph R. Fox-Rabinovitz'
AUTHOR_EMAIL = 'jfoxrabinovitz@gmail.com'

MAINTAINER = 'Joseph R. Fox-Rabinovitz'
MAINTAINER_EMAIL = 'jfoxrabinovitz@gmail.com'

CLASSIFIERS = [
    'Development Status :: 2 - Pre-Alpha',
    'Intended Audience :: Education',
    'Intended Audience :: Other Audience',
    'License :: OSI Approved :: MIT License',
    'Operating System :: Microsoft :: Windows',
    'Operating System :: POSIX :: Linux',
    'Operating System :: Unix',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3 :: Only',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'Topic :: Games/Entertainment :: Puzzle Games',
]


COMMANDS = {}


try:
    from sphinx.setup_command import BuildDoc
    COMMANDS['build_sphinx'] = BuildDoc
except ImportError:
    pass


def import_file(name, location):
    """
    Imports the specified python file as a module, without explicitly
    registering it to `sys.modules`.

    While puzzle-solvers uses Python 3 features, you are free to try to
    install it in a Python 2 environment.
    """
    if sys.version_info[0] == 2:
        # Python 2.7-
        from imp import load_source
        mod = load_source(name, location)
    elif sys.version_info < (3, 5, 0):
        # Python 3.4-
        from importlib.machinery import SourceFileLoader
        mod = SourceFileLoader(name, location).load_module()
    else:
        # Python 3.5+
        from importlib.util import spec_from_file_location, module_from_spec
        spec = spec_from_file_location(name, location)
        mod = module_from_spec(spec)
        spec.loader.exec_module(mod)
    return mod


def version_info():
    """
    Jump through some hoops to import version.py for the different
    versions of Python.

    https://stackoverflow.com/a/67692/2988730
    """
    location = join(dirname(__file__) or '.',
                    'src', 'puzzle_solvers', 'version.py')
    mod = import_file('version', location)
    return mod.__version__


def long_description():
    """
    Reads in the README and CHANGELOG files, separated by two
    newlines.
    """
    with open('README') as readme, open('CHANGELOG') as changes:
        return '%s\n\n%s' % (readme.read(), changes.read())


if __name__ == '__main__':
    setup(
        name=DIST_NAME,
        version=version_info(),
        license=LICENSE,
        description=DESCRIPTION,
        long_description_content_type='text/markdown',
        long_description=long_description(),
        author=AUTHOR,
        author_email=AUTHOR_EMAIL,
        maintainer=MAINTAINER,
        maintainer_email=MAINTAINER_EMAIL,
        classifiers=CLASSIFIERS,
        url='https://github.com/madphysicist/puzzle-solvers',
        project_urls={
            'Bugs': 'https://github.com/madphysicist/puzzle-solvers/issues',
            'Documentation': 'https://puzzle-solvers.readthedocs.io/en/latest/',
        },
        packages=[
            'puzzle_solvers',
            'puzzle_solvers.demos',
        ],
        package_dir={'': 'src'},
        install_requires=[
            'numpy >= 1.10.0',
        ],
        extras_require={
            'mpl': ['matplotlib >= 2.0'],
        },
        provides=['puzzle_solvers'],
        scripts=[],
        data_files = [('', ['LICENSE', 'README'])],
        cmdclass=COMMANDS,
    )
