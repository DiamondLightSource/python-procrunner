=====
Usage
=====

To use ProcRunner in a project::

    import procrunner
    result = procrunner.run(['/bin/ls', '/some/path/containing spaces'])

To test for successful completion::

    assert result['exitcode'] == 0

To test for no STDERR output::

    assert result['stderr'] == ''

To run with a specific environment variable set::

    result = procrunner.run(..., environment_override={ 'VARIABLE': 'value' })

To run with a specific environment::

    result = procrunner.run(..., environment={ 'VARIABLE': 'value' })
