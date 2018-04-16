==========
ProcRunner
==========


.. image:: https://img.shields.io/pypi/v/procrunner.svg
        :target: https://pypi.python.org/pypi/procrunner

.. image:: https://travis-ci.org/DiamondLightSource/python-procrunner.svg?branch=master
        :target: https://travis-ci.org/DiamondLightSource/python-procrunner

.. image:: https://ci.appveyor.com/api/projects/status/jtq4brwri5q18d0u/branch/master
        :target: https://ci.appveyor.com/project/Anthchirp/python-procrunner

.. image:: https://readthedocs.org/projects/procrunner/badge/?version=latest
        :target: https://procrunner.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

.. image:: https://pyup.io/repos/github/DiamondLightSource/python-procrunner/shield.svg
     :target: https://pyup.io/repos/github/DiamondLightSource/python-procrunner/
     :alt: Updates


Versatile utility function to run external processes


* Free software: BSD license
* Documentation: https://procrunner.readthedocs.io.


Features
--------

* runs an external process and waits for it to finish
* does not deadlock, no matter the process stdout/stderr output behaviour
* returns the exit code, stdout, stderr (separately), and the total process
  runtime as a dictionary
* process can run in a custom environment, either as a modification of
  the current environment or in a new environment from scratch
* stdin can be fed to the process, the returned dictionary contains
  information how much was read by the process
* stdout and stderr is printed by default, can be disabled
* stdout and stderr can be passed to any arbitrary function for
  live processing
* optionally enforces a time limit on the process

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
