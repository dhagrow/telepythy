from __future__ import print_function

import sys
import socket
import weakref
try:
    import queue
except ImportError:
    import Queue as queue

from . import logs
from . import sockio
from . import introspect
from .utils import start_thread

OUTPUT_MODES = ('local', 'remote', 'mirror')

log = logs.get(__name__)

class Service(object):
    def __init__(self, locs=None, filename=None, output_mode=None):
        self._locals = {}
        self._is_evaluating = False
        self._event_queues = weakref.WeakSet()

        self._code = introspect.Code(self._locals, filename)
        self._ctx = Context(self, output_mode, locs or {})

        self.reset()

    def handle(self, sock):
        try:
            while True:
                try:
                    msg = sock.recvmsg()
                except sockio.ReceiveInterrupted:
                    break
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
                elif cmd == 'complete':
                    self.complete(msg['data'])
                elif cmd == 'events':
                    for event in self.events():
                        sock.sendmsg(event)
                else:
                    log.error('unknown command: %s', cmd)
        except socket.error as e:
            log.warning('socket error: %s', e)

    def evaluate(self, source):
        self._is_evaluating = True
        try:
            self._code.evaluate(source)
        finally:
            self._is_evaluating = False
            self.add_event('done')

    def complete(self, prefix):
        matches = self._code.complete(prefix)
        self.add_event('completion', matches=matches)

    def recv_input(self, text):
        sys.stdin.write(text)

    def events(self):
        q = queue.Queue()
        self._event_queues.add(q)

        self.add_event('start', version=sys.version)

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

    def reset(self):
        self._code.reset()
        self._code.locals.update(self._ctx.env)
        self._result_count = 0

class Context(object):
    def __init__(self, service, output_mode, loc):
        self.env = {
            '__name__': '__remote__',
            '__context__': self,
            }
        self.env.update(loc)

        self._service = service

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
            sys.stdout = introspect.OutputIO(svc)
            sys.stderr = introspect.OutputIO(svc)
        elif mode == 'mirror':
            sys.stdout = introspect.OutputIO(svc, sys.__stdout__)
            sys.stderr = introspect.OutputIO(svc, sys.__stderr__)
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
