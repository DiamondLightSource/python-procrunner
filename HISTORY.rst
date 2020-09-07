=======
History
=======

2.2.0 (2020-09-07)
------------------
* Calling the run() function with unnamed arguments (other than the command
  list as the first argument) is now deprecated. As a number of arguments
  will be removed in a future version the use of unnamed arguments will
  cause future confusion. `Use explicit keyword arguments instead (#62). <https://github.com/DiamondLightSource/python-procrunner/pull/62>`_
* `The run() function debug argument has been deprecated (#63). <https://github.com/DiamondLightSource/python-procrunner/pull/63>`_
  This is only used to debug the NonBlockingStream* classes. Those are due
  to be replaced in a future release, so the argument will no longer serve
  a purpose. Debugging information remains available via standard logging
  mechanisms.
* Final version supporting Python 3.5

2.1.0 (2020-09-05)
------------------
* `Deprecated array access on the return object (#60). <https://github.com/DiamondLightSource/python-procrunner/pull/60>`_
  The return object will become a subprocess.CompletedProcess in a future
  release, which no longer allows array-based access. For a translation table
  of array elements to attributes please see the pull request linked above.
* Add a `new parameter 'raise_timeout_exceptions' (#61). <https://github.com/DiamondLightSource/python-procrunner/pull/61>`_
  When set to 'True' a subprocess.TimeoutExpired exception is raised when the
  process runtime exceeds the timeout threshold. This defaults to 'False' and
  will be set to 'True' in a future release.

2.0.0 (2020-06-24)
------------------

* Python 3.5+ only, support for Python 2.7 has been dropped
* Deprecated function alias run_process() has been removed
* Fixed a stability issue on Windows

1.1.0 (2019-11-04)
------------------

* Add Python 3.8 support, drop Python 3.4 support

1.0.2 (2019-05-20)
------------------

* Stop environment override variables leaking into the process environment

1.0.1 (2019-04-16)
------------------

* Minor fixes on the return object (implement equality,
  mark as unhashable)

1.0.0 (2019-03-25)
------------------

* Support file system path objects (PEP-519) in arguments
* Change the return object to make it similar to
  subprocess.CompletedProcess, introduced with Python 3.5+

0.9.1 (2019-02-22)
------------------

* Have deprecation warnings point to correct code locations

0.9.0 (2018-12-07)
------------------

* Trap UnicodeEncodeError when printing output. Offending characters
  are replaced and a warning is logged once. Hints at incorrectly set
  PYTHONIOENCODING.

0.8.1 (2018-12-04)
------------------

* Fix a few deprecation warnings

0.8.0 (2018-10-09)
------------------

* Add parameter working_directory to set the working directory
  of the subprocess

0.7.2 (2018-10-05)
------------------

* Officially support Python 3.7

0.7.1 (2018-09-03)
------------------

* Accept environment variable overriding with numeric values.

0.7.0 (2018-05-13)
------------------

* Unicode fixes. Fix crash on invalid UTF-8 input.
* Clarify that stdout/stderr values are returned as bytestrings.
* Callbacks receive the data decoded as UTF-8 unicode strings
  with unknown characters replaced by \ufffd (unicode replacement
  character). Same applies to printing of output.
* Mark stdin broken on Windows.

0.6.1 (2018-05-02)
------------------

* Maintenance release to add some tests for executable resolution.

0.6.0 (2018-05-02)
------------------

* Fix Win32 API executable resolution for commands containing a dot ('.') in
  addition to a file extension (say '.bat').

0.5.1 (2018-04-27)
------------------

* Fix Win32API dependency installation on Windows.

0.5.0 (2018-04-26)
------------------

* New keyword 'win32resolve' which only takes effect on Windows and is enabled
  by default. This causes procrunner to call the Win32 API FindExecutable()
  function to try and lookup non-.exe files with the corresponding name. This
  means .bat/.cmd/etc.. files can now be run without explicitly specifying
  their extension. Only supported on Python 2.7 and 3.5+.

0.4.0 (2018-04-23)
------------------

* Python 2.7 support on Windows. Python3 not yet supported on Windows.

0.3.0 (2018-04-17)
------------------

* run_process() renamed to run()
* Python3 compatibility fixes

0.2.0 (2018-03-12)
------------------

* Procrunner is now Python3 3.3-3.6 compatible.

0.1.0 (2018-03-12)
------------------

* First release on PyPI.
