from __future__ import absolute_import, division, print_function

import procrunner
import os

def test_simple_command_invocation():
  if os.name == 'nt':
    command = ['cmd.exe', '/c', 'echo', 'hello']
  else:
    command = ['echo', 'hello']

  result = procrunner.run(command)

  assert result['exitcode'] == 0
  assert result['stdout'] == b'hello' + os.linesep.encode('utf-8')
  assert result['stderr'] == b''

def test_input_encoding():
  command = ['python', '-c', 'import sys; sys.stdout.write("".join(chr(x) for x in '
             '(0x74,0x65,0x73,0x74,0xa0,0x50,0x73,0x74,0x72,0x69,0x6e,0x67,0x0a)'
             '))']
  result = procrunner.run(command)

  assert result['exitcode'] == 0
