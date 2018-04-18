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
