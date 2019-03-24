from __future__ import absolute_import, division, print_function

import copy
import mock
import os
import procrunner
import pytest
import sys


@mock.patch("procrunner._NonBlockingStreamReader")
@mock.patch("procrunner.time")
@mock.patch("procrunner.subprocess")
@mock.patch("procrunner.Pipe")
def test_run_command_aborts_after_timeout(
    mock_pipe, mock_subprocess, mock_time, mock_streamreader
):
    mock_pipe.return_value = mock.Mock(), mock.Mock()
    mock_process = mock.Mock()
    mock_process.returncode = None
    mock_subprocess.Popen.return_value = mock_process
    task = ["___"]

    with pytest.raises(RuntimeError):
        procrunner.run(task, -1, False)

    assert mock_subprocess.Popen.called
    assert mock_process.terminate.called
    assert mock_process.kill.called


@mock.patch("procrunner._NonBlockingStreamReader")
@mock.patch("procrunner.subprocess")
def test_run_command_runs_command_and_directs_pipelines(
    mock_subprocess, mock_streamreader
):
    (mock_stdout, mock_stderr) = (mock.Mock(), mock.Mock())
    mock_stdout.get_output.return_value = mock.sentinel.proc_stdout
    mock_stderr.get_output.return_value = mock.sentinel.proc_stderr
    (stream_stdout, stream_stderr) = (mock.sentinel.stdout, mock.sentinel.stderr)
    mock_process = mock.Mock()
    mock_process.stdout = stream_stdout
    mock_process.stderr = stream_stderr
    mock_process.returncode = 99
    command = ["___"]

    def streamreader_processing(*args, **kwargs):
        return {(stream_stdout,): mock_stdout, (stream_stderr,): mock_stderr}[args]

    mock_streamreader.side_effect = streamreader_processing
    mock_subprocess.Popen.return_value = mock_process

    expected = {
        "stderr": mock.sentinel.proc_stderr,
        "stdout": mock.sentinel.proc_stdout,
        "exitcode": mock_process.returncode,
        "command": tuple(command),
        "runtime": mock.ANY,
        "timeout": False,
        "time_start": mock.ANY,
        "time_end": mock.ANY,
    }

    actual = procrunner.run(
        command,
        0.5,
        False,
        callback_stdout=mock.sentinel.callback_stdout,
        callback_stderr=mock.sentinel.callback_stderr,
        working_directory=mock.sentinel.cwd,
    )

    assert mock_subprocess.Popen.called
    assert mock_subprocess.Popen.call_args[1]["env"] == os.environ
    assert mock_subprocess.Popen.call_args[1]["cwd"] == mock.sentinel.cwd
    mock_streamreader.assert_has_calls(
        [
            mock.call(
                stream_stdout,
                output=mock.ANY,
                debug=mock.ANY,
                notify=mock.ANY,
                callback=mock.sentinel.callback_stdout,
            ),
            mock.call(
                stream_stderr,
                output=mock.ANY,
                debug=mock.ANY,
                notify=mock.ANY,
                callback=mock.sentinel.callback_stderr,
            ),
        ],
        any_order=True,
    )
    assert not mock_process.terminate.called
    assert not mock_process.kill.called
    for key in expected:
        assert actual[key] == expected[key]
    assert actual.args == tuple(command)
    assert actual.returncode == mock_process.returncode
    assert actual.stdout == mock.sentinel.proc_stdout
    assert actual.stderr == mock.sentinel.proc_stderr


@mock.patch("procrunner.subprocess")
def test_default_process_environment_is_parent_environment(mock_subprocess):
    mock_subprocess.Popen.side_effect = NotImplementedError()  # cut calls short
    with pytest.raises(NotImplementedError):
        procrunner.run([mock.Mock()], -1, False)
    assert mock_subprocess.Popen.call_args[1]["env"] == os.environ


@mock.patch("procrunner.subprocess")
def test_pass_custom_environment_to_process(mock_subprocess):
    mock_subprocess.Popen.side_effect = NotImplementedError()  # cut calls short
    mock_env = {"key": mock.sentinel.key}
    # Pass an environment dictionary
    with pytest.raises(NotImplementedError):
        procrunner.run([mock.Mock()], -1, False, environment=copy.copy(mock_env))
    assert mock_subprocess.Popen.call_args[1]["env"] == mock_env


@mock.patch("procrunner.subprocess")
def test_pass_custom_environment_to_process_and_add_another_value(mock_subprocess):
    mock_subprocess.Popen.side_effect = NotImplementedError()  # cut calls short
    mock_env1 = {"keyA": mock.sentinel.keyA}
    mock_env2 = {"keyB": mock.sentinel.keyB, "number": 5}
    # Pass an environment dictionary
    with pytest.raises(NotImplementedError):
        procrunner.run(
            [mock.Mock()],
            -1,
            False,
            environment=copy.copy(mock_env1),
            environment_override=copy.copy(mock_env2),
        )
    mock_env_sum = copy.copy(mock_env1)
    mock_env_sum.update({key: str(mock_env2[key]) for key in mock_env2})
    assert mock_subprocess.Popen.call_args[1]["env"] == mock_env_sum


@mock.patch("procrunner.subprocess")
def test_use_default_process_environment_and_add_another_value(mock_subprocess):
    mock_subprocess.Popen.side_effect = NotImplementedError()  # cut calls short
    mock_env2 = {"keyB": str(mock.sentinel.keyB)}
    with pytest.raises(NotImplementedError):
        procrunner.run(
            [mock.Mock()], -1, False, environment_override=copy.copy(mock_env2)
        )
    random_environment_variable = list(os.environ)[0]
    if random_environment_variable == list(mock_env2)[0]:
        random_environment_variable = list(os.environ)[1]
    random_environment_value = os.getenv(random_environment_variable)
    assert (
        random_environment_variable
        and random_environment_variable != list(mock_env2)[0]
    )
    assert (
        mock_subprocess.Popen.call_args[1]["env"][list(mock_env2)[0]]
        == mock_env2[list(mock_env2)[0]]
    )
    assert mock_subprocess.Popen.call_args[1]["env"][
        random_environment_variable
    ] == os.getenv(random_environment_variable)


@mock.patch("procrunner.subprocess")
def test_use_default_process_environment_and_override_a_value(mock_subprocess):
    mock_subprocess.Popen.side_effect = NotImplementedError()  # cut calls short
    random_environment_variable = list(os.environ)[0]
    random_environment_value = os.getenv(random_environment_variable)
    with pytest.raises(NotImplementedError):
        procrunner.run(
            [mock.Mock()],
            -1,
            False,
            environment_override={
                random_environment_variable: "X" + random_environment_value
            },
        )
    assert (
        mock_subprocess.Popen.call_args[1]["env"][random_environment_variable]
        == "X" + random_environment_value
    )


@mock.patch("procrunner.select")
@pytest.mark.skipif(
    sys.platform == "win32",
    reason="test only relevant on platforms supporting select()",
)
def test_nonblockingstreamreader_can_read(mock_select):
    import time

    class _stream(object):
        def __init__(self):
            self.data = b""
            self.closed = False

        def write(self, string):
            self.data = self.data + string

        def read(self, n):
            if self.closed:
                return b""
            if self.data == b"":
                time.sleep(0.01)
                return b""
            if len(self.data) < n:
                data = self.data
                self.data = b""
            else:
                data = self.data[:n]
                self.data = self.data[n:]
            return data

        def close(self):
            self.closed = True

    teststream = _stream()

    def select_replacement(rlist, wlist, xlist, timeout):
        assert teststream in rlist
        if teststream.closed:
            return ([teststream], [], [])
        if teststream.data == b"":
            return ([], [], [])
        return ([teststream], [], [])

    mock_select.select = select_replacement

    streamreader = procrunner._NonBlockingStreamReader(teststream, output=False)
    assert not streamreader.has_finished()
    time.sleep(0.1)
    testdata = b"abc\n" * 1024
    teststream.write(testdata)
    time.sleep(0.2)
    teststream.close()
    time.sleep(0.1)

    assert streamreader.has_finished()
    output = streamreader.get_output()
    assert len(output) == len(testdata)
    assert output == testdata


def test_lineaggregator_aggregates_data():
    callback = mock.Mock()
    aggregator = procrunner._LineAggregator(callback=callback)

    aggregator.add(b"some")
    aggregator.add(b"string")
    callback.assert_not_called()
    aggregator.add(b"\n")
    callback.assert_called_once_with("somestring")
    callback.reset_mock()
    aggregator.add(b"more")
    aggregator.add(b"stuff")
    callback.assert_not_called()
    aggregator.flush()
    callback.assert_called_once_with("morestuff")


def test_return_object_semantics():
    ro = procrunner.ReturnObject(
        {
            "command": mock.sentinel.command,
            "exitcode": 0,
            "stdout": mock.sentinel.stdout,
            "stderr": mock.sentinel.stderr,
        }
    )
    assert ro["command"] == mock.sentinel.command
    assert ro.args == mock.sentinel.command
    assert ro["exitcode"] == 0
    assert ro.returncode == 0
    assert ro["stdout"] == mock.sentinel.stdout
    assert ro.stdout == mock.sentinel.stdout
    assert ro["stderr"] == mock.sentinel.stderr
    assert ro.stderr == mock.sentinel.stderr

    with pytest.raises(KeyError):
        ro["unknownkey"]
    ro.update({"unknownkey": mock.sentinel.key})
    assert ro["unknownkey"] == mock.sentinel.key


def test_return_object_check_function_passes_on_success():
    ro = procrunner.ReturnObject(
        {
            "command": mock.sentinel.command,
            "exitcode": 0,
            "stdout": mock.sentinel.stdout,
            "stderr": mock.sentinel.stderr,
        }
    )
    ro.check_returncode()


def test_return_object_check_function_raises_on_error():
    ro = procrunner.ReturnObject(
        {
            "command": mock.sentinel.command,
            "exitcode": 1,
            "stdout": mock.sentinel.stdout,
            "stderr": mock.sentinel.stderr,
        }
    )
    with pytest.raises(Exception) as e:
        ro.check_returncode()
    assert repr(mock.sentinel.command) in str(e.value)
    assert "1" in str(e.value)
