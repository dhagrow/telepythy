from __future__ import print_function

import sys
import code
import pprint
import weakref
try:
    import queue
except ImportError:
    import Queue as queue
from contextlib import redirect_stdout

from . import sockio
from . import logs

OUTPUT_MODES = ('local', 'remote', 'mirror')

log = logs.get(__name__)

class Service(object):
    def __init__(self, locs=None, output_mode=None):
        sys.displayhook = self.displayhook

        self._output = weakref.WeakSet()

        self._ctx = Context(self, output_mode, locs or {})

        self._locals = {}
        self._last_result = None
        self._result_count = 0
        self._result_limit = 30
        self._reset()

        self._code = code.InteractiveInterpreter(self._locals)

    def handle(self, sock):
        while True:
            msg = sock.recvmsg()
            if not msg:
                break

            cmd = msg['cmd']
            data = msg.get('data', '')
            data = data and ': ' + repr(data)
            log.debug('cmd: %s%s', cmd, data)

            if cmd == 'evaluate':
                needs_input = self.evaluate(msg['data'])
                sock.sendmsg(needs_input)
            elif cmd == 'output':
                for line in self.output():
                    sock.sendmsg(line)
            elif cmd == 'interrupt':
                self.interrupt()
            else:
                raise ValueError(cmd)

    def evaluate(self, source):
        # run
        with redirect_stdout(sys.stdout):
            needs_input = self._code.runsource(source, symbol='exec')

        if self._last_result is not None:
            value, self._last_result = self._last_result, None

            self._locals['_'] = value
            self._locals['_{}'.format(self._result_count)] = value

            print('{}: {}'.format(self._result_count, pprint.pformat(value)))

            self._result_count += 1

            # remove old results
            for i in range(max(0, self._result_count-self._result_limit)):
                self._locals.pop('_{}'.format(i), None)

        return needs_input

    def output(self):
        q = queue.Queue()
        self._output.add(q)

        while True:
            try:
                yield q.get(timeout=1)
            except queue.Empty:
                yield

    def interrupt(self):
        self._code.resetbuffer()

    def displayhook(self, value):
        self._last_result = value

    def _reset(self):
        self._locals.clear()
        self._locals.update(self._ctx.env)
        self._result_count = 0

class Context(object):
    def __init__(self, server, output_mode, loc):
        self.env = {
            '__name__': '__remote__',
            '__context__': self,
            }
        self.env.update(loc)

        self._server = server

        self._output_mode = None
        self.output_mode = output_mode or 'remote'

    @property
    def output_mode(self):
        """Determines where interpreter output is displayed.

        There are 3 valid modes:

            local  - output is only displayed locally
            remote - output is only displayed remotely
            mirror - output is displayed both locally and remotely
        """
        return self._output_mode

    @output_mode.setter
    def output_mode(self, mode):
        output = self._server._output

        if mode and mode == self._output_mode:
            return
        elif mode == 'local':
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
        elif mode == 'remote':
            sys.stdout = QueueIO(output)
            sys.stderr = QueueIO(output)
        elif mode == 'mirror':
            sys.stdout = QueueIO(output, sys.__stdout__)
            sys.stderr = QueueIO(output, sys.__stderr__)
        else:
            err = 'output_mode must be one of: {}'
            raise ValueError(err.format(', '.join(OUTPUT_MODES)))
        self._output_mode = mode

    def reset(self):
        """Clears and resets the locals environment."""
        self._server._reset()

    def __str__(self):
        return "{}(output_mode='{}', env={})".format(
            self.__class__.__name__, self.output_mode, self.env,
            )

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
        if self._mirror is not None:
            self._mirror.flush()

def serve(address, locs=None, output_mode=None):
    sockio.serve(address, Service(locs, output_mode).handle)

def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-H', '--host', default='localhost')
    parser.add_argument('-P', '--port', default=0, type=int)

    args = parser.parse_args()

    logs.init(2, log_exceptions=False)

    serve((args.host, args.port))

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
