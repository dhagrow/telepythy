from __future__ import print_function

import sys
import threading
try:
    import queue
except ImportError:
    import Queue as queue

from . import logs
from . import utils
from . import sockio
from . import introspect

OUTPUT_MODES = ('local', 'remote', 'mirror')

log = logs.get(__name__)

def serve(address, locs=None):
    Service(locs).serve(address)

def connect(address, locs=None):
    Service(locs).connect(address)

class Service(object):
    def __init__(self, locs=None, filename=None):
        self._locals = {}
        self._is_evaluating = False

        self._stop = threading.Event()
        self._events = queue.Queue()
        self.code_queue = queue.Queue()

        self._code = introspect.Code(self._locals, filename)
        self._ctx = Context(self, locs or {})

        self.reset()

    ## execution ##

    def connect(self, address):
        def _connect(svc, address):
            try:
                svc.handle(sockio.connect(address))
            except sockio.error as e:
                log.error('connection failed: %s', e)

        utils.start_thread(_connect, self, address)

        self.run()

    def serve(self, address):
        sockio.start_server(address, self.handle)
        self.run()

    def run(self):
        q = self.code_queue

        while True:
            data = q.get()
            self.evaluate(**data)

    ## commands ##

    def evaluate(self, source, notify=True):
        self._is_evaluating = True
        try:
            self._code.evaluate(source)
        finally:
            self._is_evaluating = False
            if notify:
                self.add_event('done')

    def interrupt(self):
        self._code.interrupt()

    def complete(self, prefix):
        matches = self._code.complete(prefix)
        self.add_event('completion', matches=matches)

    def events(self):
        stop = self._stop
        q = self._events

        self.add_event('start', version=sys.version)

        while not stop.is_set():
            try:
                yield q.get(timeout=1)
            except queue.Empty:
                yield

    ## handlers ##

    def handle(self, sock):
        self.add_event('start', version=sys.version)

        t_evt = utils.start_thread(self.handle_events, sock)
        t_cmd = utils.start_thread(self.handle_commands, sock)

        t_evt.join()
        t_cmd.join()

    def handle_events(self, sock):
        stop = self._stop
        events = self._events

        try:
            while not stop.is_set():
                try:
                    event = events.get(timeout=1)
                except queue.Empty:
                    sock.sendmsg(None)
                else:
                    sock.sendmsg(event)
        except sockio.error as e:
            log.warning('handle_events error: %s', repr(e))

    def handle_commands(self, sock):
        stop = self._stop

        try:
            while not stop.is_set():
                msg = sock.recvmsg()

                cmd = msg['cmd']
                data = msg.get('data')
                log.debug('cmd: %s%s', cmd, ': ' + repr(data) if data else '')

                if cmd == 'evaluate':
                    if self._is_evaluating:
                        self.recv_input(data + '\n')
                    else:
                        self.code_queue.put(data)
                elif cmd == 'interrupt':
                    self.interrupt()
                elif cmd == 'complete':
                    self.complete(data)
                else:
                    log.error('unknown command: %s', cmd)

        except sockio.ReceiveInterrupted as e:
            log.warning('handle_commands error: %s', repr(e))

    ## utils ##

    def add_event(self, name, **data):
        if name == 'output':
            log.debug('out: %r', data['text'][:100])
        else:
            log.debug('evt: %s%s', name, (data or '') and ': ' + repr(data))

        event = {'evt': name, 'data': data}
        self._events.put(event)

    def recv_input(self, text):
        sys.stdin.write(text)

    def reset(self):
        self._code.reset()
        self._code.locals.update(self._ctx.env)
        self._result_count = 0

    def stop(self):
        self._stop.set()

class Context(object):
    """Exposes a limited API to the control terminal."""
    def __init__(self, service, loc):
        self.env = {
            '__name__': '__remote__',
            '__context__': self,
            }
        self.env.update(loc)

        self._service = service

        self._output_mode = None
        self.output_mode = 'remote'

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
        self._service.reset()

    def __str__(self):
        return "{}(output_mode='{}', env={})".format(
            self.__class__.__name__, self.output_mode, self.env,
            )
