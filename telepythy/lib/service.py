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
        self._is_evaluating = False

        self._stop = threading.Event()
        self._events = queue.Queue()
        self.code_queue = queue.Queue()

        self._code = introspect.Code(locs, filename,
            lambda text: self.add_event('stdout', text=text),
            lambda text: self.add_event('stderr', text=text),
            )

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
        # clean up the environment
        sys.argv = ['']
        sys.path.insert(0, '')

        self._code.hook()
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
                        self._code.recv_input(data['source'] + '\n')
                    else:
                        self.code_queue.put(data)
                elif cmd == 'interrupt':
                    self.interrupt()
                elif cmd == 'complete':
                    self.complete(data)
                else:
                    log.error('unknown command: %s', cmd)

        except (sockio.ReceiveInterrupted, ConnectionResetError) as e:
            log.warning('handle_commands error: %s', repr(e))

    ## utils ##

    def add_event(self, name, **data):
        if name == 'stdout':
            log.debug('out: %r', data['text'][:100])
        elif name == 'stderr':
            log.debug('err: %r', data['text'][:100])
        else:
            log.debug('evt: %s%s', name, (data or '') and ': ' + repr(data))

        event = {'evt': name, 'data': data}
        self._events.put(event)

    def reset(self):
        self._code.reset()
        self._result_count = 0

    def stop(self):
        self._stop.set()
