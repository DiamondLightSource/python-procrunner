# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import codecs
import copy
import logging
import os
import select
import six
import subprocess
import sys
import time
import timeit
import warnings
from multiprocessing import Pipe
from threading import Thread

#
#  run() - A function to synchronously run an external process, supporting
#          the following features:
#
#    - runs an external process and waits for it to finish
#    - does not deadlock, no matter the process stdout/stderr output behaviour
#    - returns the exit code, stdout, stderr (separately), and the total process
#      runtime as a dictionary
#    - process can run in a custom environment, either as a modification of
#      the current environment or in a new environment from scratch
#    - stdin can be fed to the process, the returned dictionary contains
#      information how much was read by the process
#    - stdout and stderr is printed by default, can be disabled
#    - stdout and stderr can be passed to any arbitrary function for
#      live processing
#    - optionally enforces a time limit on the process
#
#
#  Usage example:
#
# import procrunner
# result = procrunner.run(['/bin/ls', '/some/path/containing spaces'])
#
#  Returns:
#
# {'command': ['/bin/ls', '/some/path/containing spaces'],
#  'exitcode': 2,
#  'runtime': 0.12990689277648926,
#  'stderr': '/bin/ls: cannot access /some/path/containing spaces: No such file or directory\n',
#  'stdout': '',
#  'time_end': '2017-11-12 19:54:49 GMT',
#  'time_start': '2017-11-12 19:54:49 GMT',
#  'timeout': False}
#

__author__ = """Markus Gerstel"""
__email__ = "scientificsoftware@diamond.ac.uk"
__version__ = "1.0.0"

logger = logging.getLogger("procrunner")
logger.addHandler(logging.NullHandler())


class _LineAggregator(object):
    """
    Buffer that can be filled with stream data and will aggregate complete
    lines. Lines can be printed or passed to an arbitrary callback function.
    The lines passed to the callback function are UTF-8 decoded and do not
    contain a trailing newline character.
    """

    def __init__(self, print_line=False, callback=None):
        """Create aggregator object."""
        self._buffer = ""
        self._print = print_line
        self._callback = callback
        self._decoder = codecs.getincrementaldecoder("utf-8")("replace")

    def add(self, data):
        """
        Add a single character to buffer. If one or more full lines are found,
        print them (if desired) and pass to callback function.
        """
        data = self._decoder.decode(data)
        if not data:
            return
        self._buffer += data
        if "\n" in data:
            to_print, remainder = self._buffer.rsplit("\n")
            if self._print:
                try:
                    print(to_print)
                except UnicodeEncodeError:
                    print(to_print.encode(sys.getdefaultencoding(), errors="replace"))
                    if not hasattr(self, "_warned"):
                        logger.warning("output encoding error, characters replaced")
                        setattr(self, "_warned", True)
            if self._callback:
                self._callback(to_print)
            self._buffer = remainder

    def flush(self):
        """Print/send any remaining data to callback function."""
        self._buffer += self._decoder.decode(b"", final=True)
        if self._buffer:
            if self._print:
                print(self._buffer)
            if self._callback:
                self._callback(self._buffer)
        self._buffer = ""


class _NonBlockingStreamReader(object):
    """Reads a stream in a thread to avoid blocking/deadlocks"""

    def __init__(self, stream, output=True, debug=False, notify=None, callback=None):
        """Creates and starts a thread which reads from a stream."""
        self._buffer = six.BytesIO()
        self._closed = False
        self._closing = False
        self._debug = debug
        self._stream = stream
        self._terminated = False

        def _thread_write_stream_to_buffer():
            la = _LineAggregator(print_line=output, callback=callback)
            char = True
            while char:
                if select.select([self._stream], [], [], 0.1)[0]:
                    char = self._stream.read(1)
                    if char:
                        self._buffer.write(char)
                        la.add(char)
                else:
                    if self._closing:
                        break
            self._terminated = True
            la.flush()
            if self._debug:
                logger.debug("Stream reader terminated")
            if notify:
                notify()

        def _thread_write_stream_to_buffer_windows():
            line = True
            while line:
                line = self._stream.readline()
                if line:
                    self._buffer.write(line)
                    if output or callback:
                        linedecode = line.decode("utf-8", "replace")
                        if output:
                            print(linedecode)
                        if callback:
                            callback(linedecode)
            self._terminated = True
            if self._debug:
                logger.debug("Stream reader terminated")
            if notify:
                notify()

        if os.name == "nt":
            self._thread = Thread(target=_thread_write_stream_to_buffer_windows)
        else:
            self._thread = Thread(target=_thread_write_stream_to_buffer)
        self._thread.daemon = True
        self._thread.start()

    def has_finished(self):
        """
        Returns whether the thread reading from the stream is still alive.
        """
        return self._terminated

    def get_output(self):
        """
        Retrieve the stored data in full.
        This call may block if the reading thread has not yet terminated.
        """
        self._closing = True
        if not self.has_finished():
            if self._debug:
                # Main thread overtook stream reading thread.
                underrun_debug_timer = timeit.default_timer()
                logger.warning("NBSR underrun")
            self._thread.join()
            if not self.has_finished():
                if self._debug:
                    logger.debug(
                        "NBSR join after %f seconds, underrun not resolved"
                        % (timeit.default_timer() - underrun_debug_timer)
                    )
                raise Exception("thread did not terminate")
            if self._debug:
                logger.debug(
                    "NBSR underrun resolved after %f seconds"
                    % (timeit.default_timer() - underrun_debug_timer)
                )
        if self._closed:
            raise Exception("streamreader double-closed")
        self._closed = True
        data = self._buffer.getvalue()
        self._buffer.close()
        return data


class _NonBlockingStreamWriter(object):
    """Writes to a stream in a thread to avoid blocking/deadlocks"""

    def __init__(self, stream, data, debug=False, notify=None):
        """Creates and starts a thread which writes data to stream."""
        self._buffer = data
        self._buffer_len = len(data)
        self._buffer_pos = 0
        self._debug = debug
        self._max_block_len = 4096
        self._stream = stream
        self._terminated = False

        def _thread_write_buffer_to_stream():
            while self._buffer_pos < self._buffer_len:
                if (self._buffer_len - self._buffer_pos) > self._max_block_len:
                    block = self._buffer[
                        self._buffer_pos : (self._buffer_pos + self._max_block_len)
                    ]
                else:
                    block = self._buffer[self._buffer_pos :]
                try:
                    self._stream.write(block)
                except IOError as e:
                    if (
                        e.errno == 32
                    ):  # broken pipe, ie. process terminated without reading entire stdin
                        self._stream.close()
                        self._terminated = True
                        if notify:
                            notify()
                        return
                    raise
                self._buffer_pos += len(block)
                if debug:
                    logger.debug("wrote %d bytes to stream" % len(block))
            self._stream.close()
            self._terminated = True
            if notify:
                notify()

        self._thread = Thread(target=_thread_write_buffer_to_stream)
        self._thread.daemon = True
        self._thread.start()

    def has_finished(self):
        """Returns whether the thread writing to the stream is still alive."""
        return self._terminated

    def bytes_sent(self):
        """Return the number of bytes written so far."""
        return self._buffer_pos

    def bytes_remaining(self):
        """Return the number of bytes still to be written."""
        return self._buffer_len - self._buffer_pos


def _path_resolve(obj):
    """
    Resolve file system path (PEP-519) objects to strings.

    :param obj: A file system path object or something else.
    :return: A string representation of a file system path object or, for
             anything that was not a file system path object, the original
             object.
    """
    if obj and hasattr(obj, "__fspath__"):
        return obj.__fspath__()
    return obj


def _windows_resolve(command):
    """
    Try and find the full path and file extension of the executable to run.
    This is so that e.g. calls to 'somescript' will point at 'somescript.cmd'
    without the need to set shell=True in the subprocess.
    If the executable contains periods it is a special case. Here the
    win32api call will fail to resolve the extension automatically, and it
    has do be done explicitly.

    :param command: The command array to be run, with the first element being
                    the command with or w/o path, with or w/o extension.
    :return: Returns the command array with the executable resolved with the
             correct extension. If the executable cannot be resolved for any
             reason the original command array is returned.
    """
    try:
        import win32api
    except ImportError:
        if (2, 8) < sys.version_info < (3, 5):
            logger.info(
                "Resolving executable names only supported on Python 2.7 and 3.5+"
            )
        else:
            logger.warning(
                "Could not resolve executable name: package win32api missing"
            )
        return command

    if not command or not isinstance(command[0], six.string_types):
        return command

    try:
        _, found_executable = win32api.FindExecutable(command[0])
        logger.debug("Resolved %s as %s", command[0], found_executable)
        return (found_executable,) + tuple(command[1:])
    except Exception as e:
        if not hasattr(e, "winerror"):
            raise
        # Keep this error message for later in case we fail to resolve the name
        logwarning = getattr(e, "strerror", str(e))

    if "." in command[0]:
        # Special case. The win32api may not properly check file extensions, so
        # try to resolve the executable explicitly.
        for extension in os.getenv("PATHEXT").split(os.pathsep):
            try:
                _, found_executable = win32api.FindExecutable(command[0] + extension)
                logger.debug("Resolved %s as %s", command[0], found_executable)
                return (found_executable,) + tuple(command[1:])
            except Exception as e:
                if not hasattr(e, "winerror"):
                    raise

    logger.warning("Error trying to resolve the executable: %s", logwarning)
    return command


if sys.version_info < (3, 5):

    class _ReturnObjectParent(object):
        def check_returncode(self):
            if self.returncode:
                raise Exception(
                    "Call %r resulted in non-zero exit code %r"
                    % (self.args, self.returncode)
                )


else:
    _ReturnObjectParent = subprocess.CompletedProcess


class ReturnObject(dict, _ReturnObjectParent):
    """
    A subprocess.CompletedProcess-like object containing the executed
    command, stdout and stderr (both as bytestrings), and the exitcode.
    Further values such as process runtime can be accessed as dictionary
    values.
    The check_returncode() function raises an exception if the process
    exited with a non-zero exit code.
    """

    def __init__(self, *arg, **kw):
        super(ReturnObject, self).__init__(*arg, **kw)
        self.args = self["command"]
        self.returncode = self["exitcode"]
        self.stdout = self["stdout"]
        self.stderr = self["stderr"]


def run(
    command,
    timeout=None,
    debug=False,
    stdin=None,
    print_stdout=True,
    print_stderr=True,
    callback_stdout=None,
    callback_stderr=None,
    environment=None,
    environment_override=None,
    win32resolve=True,
    working_directory=None,
):
    """
    Run an external process.

    File system path objects (PEP-519) are accepted in the command, environment,
    and working directory arguments.

    :param array command: Command line to be run, specified as array.
    :param timeout: Terminate program execution after this many seconds.
    :param boolean debug: Enable further debug messages.
    :param stdin: Optional string that is passed to command stdin.
    :param boolean print_stdout: Pass stdout through to sys.stdout.
    :param boolean print_stderr: Pass stderr through to sys.stderr.
    :param callback_stdout: Optional function which is called for each
                            stdout line.
    :param callback_stderr: Optional function which is called for each
                            stderr line.
    :param dict environment: The full execution environment for the command.
    :param dict environment_override: Change environment variables from the
                                      current values for command execution.
    :param boolean win32resolve: If on Windows, find the appropriate executable
                                 first. This allows running of .bat, .cmd, etc.
                                 files without explicitly specifying their
                                 extension.
    :param string working_directory: If specified, run the executable from
                                     within this working directory.
    :return: A ReturnObject() containing the executed command, stdout and stderr
             (both as bytestrings), and the exitcode. Further values such as
             process runtime can be accessed as dictionary values.
    """

    time_start = time.strftime("%Y-%m-%d %H:%M:%S GMT", time.gmtime())
    logger.debug("Starting external process: %s", command)

    if stdin is None:
        stdin_pipe = None
    else:
        assert sys.platform != "win32", "stdin argument not supported on Windows"
        stdin_pipe = subprocess.PIPE

    start_time = timeit.default_timer()
    if timeout is not None:
        max_time = start_time + timeout

    if environment is not None:
        env = {key: _path_resolve(environment[key]) for key in environment}
    else:
        env = os.environ
    if environment_override:
        env = copy.copy(env)
        env.update(
            {
                key: str(_path_resolve(environment_override[key]))
                for key in environment_override
            }
        )

    command = tuple(_path_resolve(part) for part in command)
    if win32resolve and sys.platform == "win32":
        command = _windows_resolve(command)

    p = subprocess.Popen(
        command,
        shell=False,
        cwd=_path_resolve(working_directory),
        env=env,
        stdin=stdin_pipe,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    thread_pipe_pool = []
    notifyee, notifier = Pipe(False)
    thread_pipe_pool.append(notifyee)
    stdout = _NonBlockingStreamReader(
        p.stdout,
        output=print_stdout,
        debug=debug,
        notify=notifier.close,
        callback=callback_stdout,
    )
    notifyee, notifier = Pipe(False)
    thread_pipe_pool.append(notifyee)
    stderr = _NonBlockingStreamReader(
        p.stderr,
        output=print_stderr,
        debug=debug,
        notify=notifier.close,
        callback=callback_stderr,
    )
    if stdin is not None:
        notifyee, notifier = Pipe(False)
        thread_pipe_pool.append(notifyee)
        stdin = _NonBlockingStreamWriter(
            p.stdin, data=stdin, debug=debug, notify=notifier.close
        )

    timeout_encountered = False

    while (p.returncode is None) and (
        (timeout is None) or (timeit.default_timer() < max_time)
    ):
        if debug and timeout is not None:
            logger.debug("still running (T%.2fs)" % (timeit.default_timer() - max_time))

        # wait for some time or until a stream is closed
        try:
            if thread_pipe_pool:
                # Wait for up to 0.5 seconds or for a signal on a remaining stream,
                # which could indicate that the process has terminated.
                try:
                    event = thread_pipe_pool[0].poll(0.5)
                except IOError as e:
                    # on Windows this raises "IOError: [Errno 109] The pipe has been ended"
                    # which is for all intents and purposes equivalent to a True return value.
                    if e.errno != 109:
                        raise
                    event = True
                if event:
                    # One-shot, so remove stream and watch remaining streams
                    thread_pipe_pool.pop(0)
                    if debug:
                        logger.debug("Event received from stream thread")
            else:
                time.sleep(0.5)
        except KeyboardInterrupt:
            p.kill()  # if user pressed Ctrl+C we won't be able to produce a proper report anyway
            # but at least make sure the child process dies with us
            raise

        # check if process is still running
        p.poll()

    if p.returncode is None:
        # timeout condition
        timeout_encountered = True
        if debug:
            logger.debug("timeout (T%.2fs)" % (timeit.default_timer() - max_time))

        # send terminate signal and wait some time for buffers to be read
        p.terminate()
        if thread_pipe_pool:
            thread_pipe_pool[0].poll(0.5)
        if not stdout.has_finished() or not stderr.has_finished():
            time.sleep(2)
        p.poll()

    if p.returncode is None:
        # thread still alive
        # send kill signal and wait some more time for buffers to be read
        p.kill()
        if thread_pipe_pool:
            thread_pipe_pool[0].poll(0.5)
        if not stdout.has_finished() or not stderr.has_finished():
            time.sleep(5)
        p.poll()

    if p.returncode is None:
        raise RuntimeError("Process won't terminate")

    runtime = timeit.default_timer() - start_time
    if timeout is not None:
        logger.debug(
            "Process ended after %.1f seconds with exit code %d (T%.2fs)"
            % (runtime, p.returncode, timeit.default_timer() - max_time)
        )
    else:
        logger.debug(
            "Process ended after %.1f seconds with exit code %d"
            % (runtime, p.returncode)
        )

    stdout = stdout.get_output()
    stderr = stderr.get_output()
    time_end = time.strftime("%Y-%m-%d %H:%M:%S GMT", time.gmtime())

    result = ReturnObject(
        {
            "exitcode": p.returncode,
            "command": command,
            "stdout": stdout,
            "stderr": stderr,
            "timeout": timeout_encountered,
            "runtime": runtime,
            "time_start": time_start,
            "time_end": time_end,
        }
    )
    if stdin is not None:
        result.update(
            {
                "stdin_bytes_sent": stdin.bytes_sent(),
                "stdin_bytes_remain": stdin.bytes_remaining(),
            }
        )

    return result


def run_process_dummy(command, **kwargs):
    """
    A stand-in function that returns a valid result dictionary indicating a
    successful execution. The external process is not run.
    """
    warnings.warn(
        "procrunner.run_process_dummy() is deprecated", DeprecationWarning, stacklevel=2
    )

    time_start = time.strftime("%Y-%m-%d %H:%M:%S GMT", time.gmtime())
    logger.info("run_process is disabled. Requested command: %s", command)

    result = ReturnObject(
        {
            "exitcode": 0,
            "command": command,
            "stdout": "",
            "stderr": "",
            "timeout": False,
            "runtime": 0,
            "time_start": time_start,
            "time_end": time_start,
        }
    )
    if kwargs.get("stdin") is not None:
        result.update(
            {"stdin_bytes_sent": len(kwargs["stdin"]), "stdin_bytes_remain": 0}
        )
    return result


def run_process(*args, **kwargs):
    """API used up to version 0.2.0."""
    warnings.warn(
        "procrunner.run_process() is deprecated and has been renamed to run()",
        DeprecationWarning,
        stacklevel=2,
    )
    return run(*args, **kwargs)
