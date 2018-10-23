from gevent import monkey
monkey.patch_all()

import io
import sys
import code
import contextlib

import sage
import gevent
from gevent import queue

URL = 'tcp://localhost:6336'

def main():
    try:
        TeleServer(URL).serve()
    except KeyboardInterrupt:
        pass

class TeleServer(sage.Server):
    def __init__(self, *args, **kwargs):
        super(TeleServer, self).__init__(*args, **kwargs)
        self._output = queue.Queue()
        self._locals = {}
        self._code = code.InteractiveConsole(self._locals)

        self._reset()

    @sage.command()
    def evaluate(self, source):
        return self._code.push(source)

    @sage.command()
    @sage.command_stream()
    def output(self):
        for line in self._output:
            yield line

    def _reset(self):
        self._locals.clear()
        self._locals.update({
            '__name__': '__remote__',
            '__tele__': Environment(self),
            })

class Environment(object):
    def __init__(self, server):
        self._server = server
        self._stdout = None
        self._stderr = None

    def capture_on(self):
        self._stdout, sys.stdout = sys.stdout, Capture(self._server._output)
        self._stderr, sys.stderr = sys.stderr, Capture(self._server._output)

    def capture_off(self):
        sys.stdout = self._stdout or sys.__stdout__
        sys.stderr = self._stderr or sys.__stderr__

    def reset(self):
        self._server._reset()

class Capture(object):
    def __init__(self, q):
        self._q = q

    def write(self, s):
        if isinstance(s, bytes):
            s = s.decode('utf8')
        self._q.put(s)

if __name__ == '__main__':
    main()
