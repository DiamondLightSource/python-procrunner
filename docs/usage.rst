=====
Usage
=====

To use ProcRunner in a project::

    import procrunner
    result = procrunner.run(['/bin/ls', '/some/path/containing spaces'])

To test for successful completion::

    assert not result.returncode
    assert result.returncode == 0  # alternatively
    result.check_returncode()  # raises subprocess.CalledProcessError()

To test for no STDERR output::

    assert not result.stderr
    assert result.stderr == b''  # alternatively

To run with a specific environment variable set::

    result = procrunner.run(..., environment_override={ 'VARIABLE': 'value' })

To run with a specific environment::

    result = procrunner.run(..., environment={ 'VARIABLE': 'value' })

To run in a specific directory::

    result = procrunner.run(..., working_directory='/some/path')
