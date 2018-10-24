from gevent import monkey
monkey.patch_all()

import io
import sys
import code
import contextlib

import sage
from gevent import queue

URL = 'tcp://localhost:6336'
OUTPUT_MODES = ('off', 'capture', 'mirror')

def main():
    try:
        TeleServer(URL).serve()
    except KeyboardInterrupt:
        pass

class TeleServer(sage.Server):
    def __init__(self, *args, **kwargs):
        output_mode = kwargs.pop('output_mode', 'mirror')
        super(TeleServer, self).__init__(*args, **kwargs)

        self._output_q = queue.Queue()
        self._env = {
            '__name__': '__remote__',
            '__tele__': Environment(self, output_mode),
            }

        self._locals = {}
        self._code = code.InteractiveConsole(self._locals)
        self._reset()

    @sage.command()
    def evaluate(self, source):
        return self._code.push(source)

    @sage.command()
    @sage.command_stream()
    def output(self):
        while True:
            yield self._output_q.get()

    def _reset(self):
        self._locals.clear()
        self._locals.update(self._env)

class Environment(object):
    def __init__(self, server, output_mode):
        self._server = server
        self._stdout = sys.__stdout__
        self._stderr = sys.__stderr__

        self._output_mode = None
        self.output_mode = output_mode

    @property
    def output_mode(self):
        return self._output_mode

    @output_mode.setter
    def output_mode(self, mode):
        q = self._server._output_q

        if mode == self._output_mode:
            return
        elif mode == 'off':
            sys.stdout = self._stdout or sys.__stdout__
            sys.stderr = self._stderr or sys.__stderr__
        elif mode == 'capture':
            self.output_mode = 'off'
            self._stdout, sys.stdout = sys.stdout, Capture(q)
            self._stderr, sys.stderr = sys.stderr, Capture(q)
        elif mode == 'mirror':
            self.output_mode = 'off'
            self._stdout, sys.stdout = sys.stdout, Capture(q, sys.stdout)
            self._stderr, sys.stderr = sys.stderr, Capture(q, sys.stderr)
        else:
            err = 'output_mode must be one of: {}'
            raise ValueError(err.format(', '.join(OUTPUT_MODES)))
        self._output_mode = mode

    def reset(self):
        self._server._reset(self._output_mode)

class Capture(object):
    def __init__(self, q, mirror=None):
        self._q = q
        self._mirror = mirror

    def write(self, s):
        if self._mirror is not None:
            self._mirror.write(s)
        if isinstance(s, bytes):
            s = s.decode('utf8')
        self._q.put(s)

if __name__ == '__main__':
    main()
