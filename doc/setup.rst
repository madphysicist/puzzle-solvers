.. puzzle-solvers: a library of tools for solving puzzles

.. Copyright (C) 2019  Joseph R. Fox-Rabinovitz <jfoxrabinovitz at gmail dot com>

.. Permission is hereby granted, free of charge, to any person obtaining a copy
.. of this software and associated documentation files (the "Software"), to
.. deal in the Software without restriction, including without limitation the
.. rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
.. sell copies of the Software, and to permit persons to whom the Software is
.. furnished to do so, subject to the following conditions:

.. The above copyright notice and this permission notice shall be included in
.. all copies or substantial portions of the Software.

.. THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
.. IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
.. FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
.. AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
.. LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
.. FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
.. IN THE SOFTWARE.

.. Author: Joseph Fox-Rabinovitz <jfoxrabinovitz at gmail dot com>
.. Version: 28 May 2019: Initial Coding


.. _setup:

===========
Setup Guide
===========

This document explains how to obtain, install, and use Puzzle Solvers.

.. _setup-toc:

.. contents:: Contents:
   :depth: 2
   :local:


.. _setup-install:

-------------------
Getting the Package
-------------------


.. _setup-install-pypi:

PyPI
====

Puzzle Solvers is available on `pypi`_, so the recommended way to install it
is ::

    pip install puzzle-solvers

`matplotlib`_ is an optional dependency, which can be installed using the
``mpl`` extra::

    pip install puzzle-solvers[mpl]


.. _installation-source:

Source
======

You can obtain a copy of the Puzzle Solvers source code from `GitHub`_ at
https://github.com/madphysicist/puzzle-solvers. The simplest way to keep up
with changes is to clone the repo::

    git clone git@github.com:madphysicist/puzzle-solvers.git

You can also download a zip archive of the latest repository code from
https://github.com/madphysicist/puzzle-solvers/archive/master.zip.

Puzzle Solvers uses `setuptools`_, so you can install it from source as well.
Once you have a copy of the source distribution, run ::

    python setup.py install

from the project root directory, with the appropriate privileges.

You can do the same thing with :program:`pip` if you prefer. Any of the
following should work, depending on how you obtained your distribution ::

    pip install git+<URL>/puzzle-solvers.git@master[mpl]  # For a remote git repository
    pip install puzzle-solvers.zip[mpl]                   # For an archived file
    pip install puzzle-solvers[mpl]                       # For an unpacked folder or repo


.. _setup-usage:

-----
Usage
-----

Puzzle Solvers is intended primarily as a library. Once it is properly
installed, it can be imported as any normal python library::

    import puzzle_solvers

The individual :ref:`modules <modindex>` provide tools for specific puzzle
types.


.. _setup-demos:

-----
Demos
-----

Each module in :py:mod:`puzzle_solvers` comes with a corresponding demo in
:py:mod:`puzzle_solvers.demos`. Each demo is a standalone script that is
intended to be run as a packaged module. For example::

    python -m puzzle_solvers.demos.elimination


.. _setup-tests:

-----
Tests
-----

Puzzle Solvers does not currently have any formal unit tests available.
However, running through all of the demos and tutorials serves as a
non-automated set of tests, since they exercise nearly every aspect of the
solvers. Eventually, `pytest`_\ -compatible tests will be added in the
:py:mod:`~puzzle_solvers.tests` package.


.. _setup-docs:

-------------
Documentation
-------------


.. _setup-docs-online:

Online
======

The documentation is available online at https://puzzle-solvers/readthedocs.io.


.. _setup-docs-build:

Building
========

If you intend to build the documentation, you must have `Sphinx`_ installed,
and optionally the `ReadTheDocs Theme`_ extension for optimal viewing.

The documentation can be built from the complete source distribution by using
the specially defined command::

    python setup.py build_sphinx

Alternatively (perhaps preferably), it can be built using the provided
Makefile/Batch script::

    cd doc
    make html

Both options work on Windows and Unix-like systems that have :program:`make`
installed. The Windows version does not require :program:`make`. On Linux you
can also do ::

    make -C doc html

The documentation is not present in the `PyPI`_ source distributions, only
directly from `GitHub`_.


.. include:: /link-defs.rst
