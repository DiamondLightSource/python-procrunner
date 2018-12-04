from __future__ import absolute_import, division, print_function

import os
import sys

import procrunner
import pytest


def test_simple_command_invocation():
    if os.name == "nt":
        command = ["cmd.exe", "/c", "echo", "hello"]
    else:
        command = ["echo", "hello"]

    result = procrunner.run(command)

    assert result["exitcode"] == 0
    assert result["stdout"] == b"hello" + os.linesep.encode("utf-8")
    assert result["stderr"] == b""


def test_decode_invalid_utf8_input(capsys):
    test_string = b"test\xa0string\n"
    if os.name == "nt":
        pytest.xfail("Test requires stdin feature which does not work on Windows")
        command = ["cmd.exe", "/c", "type", "CON"]
    else:
        command = ["cat"]
    result = procrunner.run(command, stdin=test_string)
    assert result["exitcode"] == 0
    assert not result["stderr"]
    if os.name == "nt":
        # Windows modifies line endings
        assert result["stdout"] == test_string[:-1] + b"\r\n"
    else:
        assert result["stdout"] == test_string
    out, err = capsys.readouterr()
    assert out == u"test\ufffdstring\n"
    assert err == u""


def test_running_wget(tmpdir):
    tmpdir.chdir()
    command = ["wget", "https://www.google.com", "-O", "-"]
    try:
        result = procrunner.run(command)
    except OSError as e:
        if e.errno == 2:
            pytest.skip("wget not available")
        raise
    assert result["exitcode"] == 0
    assert b"http" in result["stderr"]
    assert b"google" in result["stdout"]
