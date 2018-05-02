=======
History
=======

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
