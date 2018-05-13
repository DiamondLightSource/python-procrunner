from __future__ import absolute_import, division, print_function

import os
import sys

import procrunner
import pytest

def test_simple_command_invocation():
  if os.name == 'nt':
    command = ['cmd.exe', '/c', 'echo', 'hello']
  else:
    command = ['echo', 'hello']

  result = procrunner.run(command)

  assert result['exitcode'] == 0
  assert result['stdout'] == b'hello' + os.linesep.encode('utf-8')
  assert result['stderr'] == b''

def test_decode_invalid_utf8_input(capsys):
  command = [sys.executable, '-c', 'import sys; sys.stdout.write("".join(chr(x) for x in '
             '(0x74,0x65,0x73,0x74,0xa0,0x73,0x74,0x72,0x69,0x6e,0x67,0x0a)'
             '))']
  result = procrunner.run(command)
  assert result['exitcode'] == 0
  assert not result['stderr']
  assert result['stdout'] == b'test\xa0string\n'
  out, err = capsys.readouterr()
  assert out == u'test\ufffdstring\n'
  assert err == u''

def test_running_wget(tmpdir):
  tmpdir.chdir()
  command = ['wget', 'https://www.google.com', '-O', '-']
  try:
    result = procrunner.run(command)
  except OSError as e:
    if e.errno == 2:
      pytest.skip('wget not available')
    raise
  assert result['exitcode'] == 0
  assert b'http' in result['stderr']
  assert b'google' in result['stdout']
