==========
ProcRunner
==========


.. image:: https://img.shields.io/pypi/v/procrunner.svg
        :target: https://pypi.python.org/pypi/procrunner
        :alt: PyPI release

.. image:: https://img.shields.io/conda/vn/conda-forge/procrunner.svg
        :target: https://anaconda.org/conda-forge/procrunner
        :alt: Conda Version

.. image:: https://dev.azure.com/DLS-tooling/procrunner/_apis/build/status/CI?branchName=master
        :target: https://github.com/DiamondLightSource/python-procrunner/commits/master
        :alt: Build status

.. image:: https://ci.appveyor.com/api/projects/status/jtq4brwri5q18d0u/branch/master
        :target: https://ci.appveyor.com/project/Anthchirp/python-procrunner
        :alt: Build status

.. image:: https://readthedocs.org/projects/procrunner/badge/?version=latest
        :target: https://procrunner.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

.. image:: https://img.shields.io/pypi/pyversions/procrunner.svg
        :target: https://pypi.python.org/pypi/procrunner
        :alt: Supported Python versions

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
        :target: https://github.com/ambv/black
        :alt: Code style: black

Versatile utility function to run external processes

* Free software: BSD license
* Documentation: https://procrunner.readthedocs.io.


Features
--------

* runs an external process and waits for it to finish
* does not deadlock, no matter the process stdout/stderr output behaviour
* returns the exit code, stdout, stderr (separately, both as bytestrings),
  as a subprocess.CompletedProcess object
* process can run in a custom environment, either as a modification of
  the current environment or in a new environment from scratch
* stdin can be fed to the process
* stdout and stderr is printed by default, can be disabled
* stdout and stderr can be passed to any arbitrary function for
  live processing (separately, both as unicode strings)
* optionally enforces a time limit on the process, raising a
  subprocess.TimeoutExpired exception if it is exceeded.


Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
