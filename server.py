import io
import sys
import code
import weakref
import contextlib
from collections import abc
try:
    import queue
except ImportError:
    import Queue as queue

import sage

URL = 'tcp://localhost:6336'
OUTPUT_MODES = ('off', 'capture', 'mirror')

class TeleServer(sage.Server):
    def __init__(self, *args, **kwargs):
        output_mode = kwargs.pop('output_mode', 'mirror')
        super(TeleServer, self).__init__(*args, **kwargs)

        self._output = weakref.WeakSet()

        self._env = Environment(self, output_mode)
        self._locals = {}
        self._reset()

        self._code = code.InteractiveInterpreter(self._locals)

    @sage.command()
    def evaluate(self, source):
        if not source.strip():
            return False, '', ''
        if not source.endswith('\n'):
            source += '\n'
        with capture() as (stdout, stderr):
            try:
                code = compile(source, '<remote>', 'single')
            except (OverflowError, SyntaxError, ValueError):
                self._code.showsyntaxerror('<remote>')
            else:
                self._code.runcode(code)
        return False, stdout.getvalue(), stderr.getvalue()

    @sage.command()
    def output(self):
        q = queue.Queue()
        self._output.add(q)

        while True:
            try:
                yield q.get(timeout=1)
            except queue.Empty:
                if self.is_client_closed():
                    break

    @sage.command()
    def interrupt(self):
        self._code.resetbuffer()

    def _reset(self):
        self._locals.clear()
        self._locals.update(self._env)

class Environment(abc.MutableMapping):
    def __init__(self, server, output_mode):
        self._env = {
            '__name__': '__remote__',
            '__tele__': self,
            }

        self._server = server
        self._stdout = sys.__stdout__
        self._stderr = sys.__stderr__

        self._output_mode = None
        self.output_mode = output_mode

    def __len__(self):
        return len(self._env)

    def __iter__(self):
        return iter(self._env)

    def __getitem__(self, key):
        return self._env[key]

    def __setitem__(self, key, value):
        self._env[key] = value

    def __delitem__(self, key):
        del self._env[key]

    @property
    def output_mode(self):
        return self._output_mode

    @output_mode.setter
    def output_mode(self, mode):
        output = self._server._output

        if mode == self._output_mode:
            return
        elif mode == 'off':
            sys.stdout = self._stdout or sys.__stdout__
            sys.stderr = self._stderr or sys.__stderr__
        elif mode == 'capture':
            self.output_mode = 'off'
            self._stdout, sys.stdout = sys.stdout, QueueIO(output)
            self._stderr, sys.stderr = sys.stderr, QueueIO(output)
        elif mode == 'mirror':
            self.output_mode = 'off'
            self._stdout, sys.stdout = sys.stdout, QueueIO(output, sys.stdout)
            self._stderr, sys.stderr = sys.stderr, QueueIO(output, sys.stderr)
        else:
            err = 'output_mode must be one of: {}'
            raise ValueError(err.format(', '.join(OUTPUT_MODES)))
        self._output_mode = mode

    def reset(self):
        self._server._reset(self._output_mode)

@contextlib.contextmanager
def capture():
    out = io.StringIO()
    err = io.StringIO()
    org_out, sys.stdout = sys.stdout, out
    org_err, sys.stderr = sys.stderr, err
    try:
        yield out, err
    finally:
        sys.stdout = org_out
        sys.stderr = org_err

class QueueIO(object):
    def __init__(self, output, mirror=None):
        self._output = output
        self._mirror = mirror

    def write(self, s):
        if self._mirror is not None:
            self._mirror.write(s)
        if isinstance(s, bytes):
            s = s.decode('utf8')
        for q in self._output:
            q.put(s)

    def flush(self):
        pass

def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--url', default=URL,
        help='the server bind URL (default=%(default)s)')

    args = parser.parse_args()
    TeleServer(args.url).serve()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
