from __future__ import print_function

import ast
import sys
import code
import pprint
import weakref
import threading
import traceback
import collections
try:
    import queue
except ImportError:
    import Queue as queue

from . import logs
from . import sockio
from .threads import start_thread

OUTPUT_MODES = ('local', 'remote', 'mirror')

log = logs.get(__name__)

try:
    range = xrange
except NameError:
    pass

class Service(object):
    def __init__(self, locs=None, filename=None, output_mode=None):
        sys.displayhook = self.displayhook

        self._event_queues = weakref.WeakSet()

        self._ctx = Context(self, output_mode, locs or {})

        self._locals = {}
        self._filename = filename or '<telepythy>'
        self._is_evaluating = False
        self._last_result = None
        self._result_count = 0
        self._result_limit = 30
        self._reset()

        self._code = code.InteractiveInterpreter(self._locals)

    def handle(self, sock):
        try:
            while True:
                msg = sock.recvmsg()
                if not msg:
                    break

                cmd = msg['cmd']
                data = msg.get('data', '')
                data = data and ': ' + repr(data)
                log.debug('cmd: %s%s', cmd, data)

                if cmd == 'evaluate':
                    if self._is_evaluating:
                        self.recv_input(msg['data'] + '\n')
                    else:
                        start_thread(self.evaluate, msg['data'])
                elif cmd == 'events':
                    for event in self.events():
                        sock.sendmsg(event)
                elif cmd == 'interrupt':
                    self.interrupt()
                else:
                    raise ValueError(cmd)
        except Exception as e:
            log.warning('socket error: %s', e)

    def evaluate(self, source):
        fname = self._filename

        self._is_evaluating = True
        try:
            mod = compile(source, fname, 'exec', ast.PyCF_ONLY_AST)
            inter = ast.Interactive(mod.body)
            codeob = compile(inter, fname, 'single')

            try:
                exec(codeob, self._locals)
            except:
                traceback.print_exc()

            self._store_result()

        finally:
            self._is_evaluating = False
            self.add_event('done')

    def _store_result(self):
        if self._last_result is None:
            return

        # pop
        result, self._last_result = self._last_result, None

        self._locals['_'] = result
        self._locals['_{}'.format(self._result_count)] = result

        print('{}: {}'.format(self._result_count, pprint.pformat(result)))

        self._result_count += 1

        # remove old results
        for i in range(max(0, self._result_count-self._result_limit)):
            self._locals.pop('_{}'.format(i), None)

    def recv_input(self, text):
        sys.stdin.write(text)

    def events(self):
        q = queue.Queue()
        self._event_queues.add(q)

        while True:
            try:
                yield q.get(timeout=1)
            except queue.Empty:
                yield

    def add_event(self, name, **data):
        if name == 'output':
            log.debug('out: %r', data['text'][:100])
        else:
            log.debug('evt: %s%s', name, (data or '') and ': ' + repr(data))

        event = {'evt': name, 'data': data}
        for q in self._event_queues:
            q.put(event)

    def interrupt(self):
        self._code.resetbuffer()

    def displayhook(self, value):
        self._last_result = value

    def _reset(self):
        self._locals.clear()
        self._locals.update(self._ctx.env)
        self._result_count = 0

class Context(object):
    def __init__(self, service, output_mode, loc):
        self.env = {
            '__name__': '__remote__',
            '__context__': self,
            }
        self.env.update(loc)

        self._service = service

        sys.stdin = InputIO()

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
        svc = self._service

        if mode and mode == self._output_mode:
            return
        elif mode == 'local':
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
        elif mode == 'remote':
            sys.stdout = OutputIO(svc)
            sys.stderr = OutputIO(svc)
        elif mode == 'mirror':
            sys.stdout = OutputIO(svc, sys.__stdout__)
            sys.stderr = OutputIO(svc, sys.__stderr__)
        else:
            err = 'output_mode must be one of: {}'
            raise ValueError(err.format(', '.join(OUTPUT_MODES)))
        self._output_mode = mode

    def reset(self):
        """Clears and resets the locals environment."""
        self._service._reset()

    def __str__(self):
        return "{}(output_mode='{}', env={})".format(
            self.__class__.__name__, self.output_mode, self.env,
            )

class InputIO:
    def __init__(self):
        self._buffer = collections.deque()
        self._ready = threading.Event()

    def read(self, size):
        buf = self._buffer
        ready = self._ready

        while True:
            if len(buf) < size:
                ready.wait()
                ready.clear()
                continue
            return ''.join(buf.popleft() for _ in range(size))

    def readline(self):
        buf = []
        while True:
            c = self.read(1)
            if c == '\n':
                return ''.join(buf)
            else:
                buf.append(c)

    def write(self, data):
        self._buffer.extend(data)
        self._ready.set()

class OutputIO(object):
    def __init__(self, service, mirror=None):
        self._service = service
        self._mirror = mirror

    def write(self, s):
        if self._mirror is not None:
            self._mirror.write(s)
        if isinstance(s, bytes):
            s = s.decode('utf8')
        self._service.add_event('output', text=s)

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
