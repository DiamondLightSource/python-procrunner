import os
import subprocess
import sys
import timeit

import procrunner
import pytest


def test_simple_command_invocation():
    if os.name == "nt":
        command = ["cmd.exe", "/c", "echo", "hello"]
    else:
        command = ["echo", "hello"]

    result = procrunner.run(command)

    assert result.returncode == 0
    assert result.stdout == b"hello" + os.linesep.encode("utf-8")
    assert result.stderr == b""


def test_decode_invalid_utf8_input(capsys):
    test_string = b"test\xa0string\n"
    if os.name == "nt":
        pytest.xfail("Test requires stdin feature which does not work on Windows")
        command = ["cmd.exe", "/c", "type", "CON"]
    else:
        command = ["cat"]
    result = procrunner.run(command, stdin=test_string)
    assert result.returncode == 0
    assert not result.stderr
    if os.name == "nt":
        # Windows modifies line endings
        assert result.stdout == test_string[:-1] + b"\r\n"
    else:
        assert result.stdout == test_string
    out, err = capsys.readouterr()
    assert out == "test\ufffdstring\n"
    assert err == ""


def test_running_wget(tmpdir):
    tmpdir.chdir()
    command = ["wget", "https://www.google.com", "-O", "-"]
    try:
        result = procrunner.run(command)
    except OSError as e:
        if e.errno == 2:
            pytest.skip("wget not available")
        raise
    assert result.returncode == 0
    assert b"http" in result.stderr
    assert b"google" in result.stdout


def test_path_object_resolution(tmpdir):
    sentinel_value = b"sentinel"
    tmpdir.join("tempfile").write(sentinel_value)
    tmpdir.join("reader.py").write("print(open('tempfile').read())")
    assert "LEAK_DETECTOR" not in os.environ
    result = procrunner.run(
        [sys.executable, tmpdir.join("reader.py")],
        environment_override={"PYTHONHASHSEED": "random", "LEAK_DETECTOR": "1"},
        working_directory=tmpdir,
    )
    assert result.returncode == 0
    assert not result.stderr
    assert sentinel_value == result.stdout.strip()
    assert (
        "LEAK_DETECTOR" not in os.environ
    ), "overridden environment variable leaked into parent process"


def test_timeout_behaviour_legacy(tmp_path):
    start = timeit.default_timer()
    try:
        with pytest.warns(DeprecationWarning, match="timeout"):
            result = procrunner.run(
                [sys.executable, "-c", "import time; time.sleep(5)"],
                timeout=0.1,
                working_directory=tmp_path,
                raise_timeout_exception=False,
            )
    except RuntimeError:
        # This test sometimes fails with a RuntimeError.
        runtime = timeit.default_timer() - start
        assert runtime < 3
        return
    runtime = timeit.default_timer() - start
    with pytest.warns(DeprecationWarning, match="\\.timeout"):
        assert result.timeout
    assert runtime < 3
    assert not result.stdout
    assert not result.stderr
    assert result.returncode


def test_timeout_behaviour(tmp_path):
    command = (sys.executable, "-c", "import time; time.sleep(5)")
    start = timeit.default_timer()
    try:
        with pytest.raises(subprocess.TimeoutExpired) as te:
            procrunner.run(
                command,
                timeout=0.1,
                working_directory=tmp_path,
                raise_timeout_exception=True,
            )
    except RuntimeError:
        # This test sometimes fails with a RuntimeError.
        runtime = timeit.default_timer() - start
        assert runtime < 3
        return
    runtime = timeit.default_timer() - start
    assert runtime < 3
    assert te.value.stdout == b""
    assert te.value.stderr == b""
    assert te.value.timeout == 0.1
    assert te.value.cmd == command


def test_argument_deprecation(tmp_path):
    with pytest.warns(DeprecationWarning, match="keyword arguments"):
        result = procrunner.run(
            [sys.executable, "-V"],
            None,
            working_directory=tmp_path,
        )
    assert not result.returncode
    assert result.stderr or result.stdout
