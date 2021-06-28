import os
import sys

import pytest

import procrunner


def PEP519(path):
    class MockObject:
        @staticmethod
        def __fspath__():
            return path

        def __repr__(self):
            return "<path object: %s>" % path

    return MockObject()


@pytest.mark.parametrize(
    "obj",
    (
        None,
        True,
        False,
        1,
        1.0,
        ["thing"],
        {},
        {1},
        {"thing": "thing"},
        "string",
        b"bytes",
        RuntimeError(),
        ["thing", PEP519("thing")],  # no recursive resolution
    ),
)
def test_path_object_resolution_for_non_path_objs_does_not_modify_objects(obj):
    assert procrunner._path_resolve(obj) is obj


def test_path_object_resolution_of_path_objects():
    assert procrunner._path_resolve(PEP519("thing")) == "thing"


@pytest.mark.skipif(sys.platform != "win32", reason="windows specific test only")
def test_name_resolution_for_simple_exe():
    command = ["cmd.exe", "/c", "echo", "hello"]

    resolved = procrunner._windows_resolve(command)

    # command should be replaced with full path to cmd.exe
    assert resolved[0].lower().endswith("\\cmd.exe")
    assert os.path.exists(resolved[0])

    # parameters are unchanged
    assert resolved[1:] == tuple(command[1:])


@pytest.mark.skipif(sys.platform != "win32", reason="windows specific test only")
def test_name_resolution_for_complex_cases(tmp_path):
    bat = "simple_bat_extension"
    cmd = "simple_cmd_extension"
    exe = "simple_exe_extension"
    dotshort = "more_complex_filename_with_a.dot"
    dotlong = "more_complex_filename.withadot"

    (tmp_path / (bat + ".bat")).touch()
    (tmp_path / (cmd + ".cmd")).touch()
    (tmp_path / (exe + ".exe")).touch()
    (tmp_path / (dotshort + ".bat")).touch()
    (tmp_path / (dotlong + ".cmd")).touch()

    def is_valid(command):
        assert len(command) == 1
        assert os.path.exists(tmp_path / command[0])

    is_valid(procrunner._windows_resolve([bat], path=os.fspath(tmp_path)))
    is_valid(procrunner._windows_resolve([cmd], path=os.fspath(tmp_path)))
    is_valid(procrunner._windows_resolve([exe], path=os.fspath(tmp_path)))
    is_valid(procrunner._windows_resolve([dotshort], path=os.fspath(tmp_path)))
    is_valid(procrunner._windows_resolve([dotlong], path=os.fspath(tmp_path)))
