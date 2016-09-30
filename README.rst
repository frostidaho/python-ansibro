========
Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests
      - |
        | |codecov|
    * - package
      - |version| |downloads| |wheel| |supported-versions| |supported-implementations|

.. |docs| image:: https://readthedocs.org/projects/python-ansibro/badge/?style=flat
    :target: https://readthedocs.org/projects/python-ansibro
    :alt: Documentation Status

.. |codecov| image:: https://codecov.io/github/frostidaho/python-ansibro/coverage.svg?branch=master
    :alt: Coverage Status
    :target: https://codecov.io/github/frostidaho/python-ansibro

.. |version| image:: https://img.shields.io/pypi/v/ansibro.svg?style=flat
    :alt: PyPI Package latest release
    :target: https://pypi.python.org/pypi/ansibro

.. |downloads| image:: https://img.shields.io/pypi/dm/ansibro.svg?style=flat
    :alt: PyPI Package monthly downloads
    :target: https://pypi.python.org/pypi/ansibro

.. |wheel| image:: https://img.shields.io/pypi/wheel/ansibro.svg?style=flat
    :alt: PyPI Wheel
    :target: https://pypi.python.org/pypi/ansibro

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/ansibro.svg?style=flat
    :alt: Supported versions
    :target: https://pypi.python.org/pypi/ansibro

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/ansibro.svg?style=flat
    :alt: Supported implementations
    :target: https://pypi.python.org/pypi/ansibro


.. end-badges

An ansible wrapper

* Free software: BSD license

Installation
============

::

    pip install ansibro

Documentation
=============

https://python-ansibro.readthedocs.io/

Development
===========

To run the all tests run::

    tox

Note, to combine the coverage data from all the tox environments run:

.. list-table::
    :widths: 10 90
    :stub-columns: 1

    - - Windows
      - ::

            set PYTEST_ADDOPTS=--cov-append
            tox

    - - Other
      - ::

            PYTEST_ADDOPTS=--cov-append tox
