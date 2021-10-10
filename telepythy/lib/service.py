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

TIMEOUT = 0.1

log = logs.get(__name__)

class Service(object):
    def __init__(self, locs=None, filename=None, embed_mode=True):
        self._timeout = TIMEOUT

        self._stop = threading.Event()
        self._shutdown = threading.Event()

        self._events = queue.Queue()
        self._code_queue = queue.Queue()

        self._is_evaluating = False

        if not embed_mode:
            # set up a shell environment
            locs = locs or {}
            locs.setdefault('__name__', '__main__')

            sys.argv = ['']
            if not sys.path or sys.path[0] != '':
                sys.path.insert(0, '')

        self._code = introspect.Code(locs, filename,
            lambda text: self.add_event('stdout', text=text),
            lambda text: self.add_event('stderr', text=text),
            )

    ## execution ##

    def connect(self, address):
        client, _addr = sockio.start_client(address, self._handle)
        try:
            self.run()
        finally:
            client.stop()
            client.join()

    def serve(self, address):
        server, _addr = sockio.start_server(address, self._handle)
        try:
            self.run()
        finally:
            server.stop()
            server.join()

    def run(self):
        shutdown = self._shutdown
        shutdown.clear()

        q = self._code_queue
        timeout = self._timeout

        with self._code.hooked():
            while not shutdown.is_set():
                try:
                    data = q.get(timeout=timeout)
                except queue.Empty:
                    continue
                self.evaluate(**data)

    def shutdown(self):
        self._shutdown.set()

    ## interpreter ##

    @property
    def locals(self):
        return self._code.locals

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

    def reset(self):
        self._code.reset()

    ## handlers ##

    def add_event(self, name, **data):
        if name == 'stdout':
            log.debug('out: %r', data['text'][:100])
        elif name == 'stderr':
            log.debug('err: %r', data['text'][:100])
        else:
            log.debug('evt: %s%s', name, (data or '') and ': ' + repr(data))

        event = {'evt': name, 'data': data}
        self._events.put(event)

    def _handle(self, sock):
        self._stop.clear()

        self.add_event('start', version=sys.version)

        t_evt = utils.start_thread(self._handle_events, sock)
        t_cmd = utils.start_thread(self._handle_commands, sock)

        t_evt.join()
        t_cmd.join()

    def _handle_events(self, sock):
        stop = self._stop
        events = self._events
        timeout = self._timeout

        try:
            while not stop.is_set():
                try:
                    event = events.get(timeout=timeout)
                except queue.Empty:
                    sock.sendmsg(None)
                else:
                    sock.sendmsg(event)
        except sockio.error as e:
            log.error('handle_events error: %s', repr(e))
            stop.set()

    def _handle_commands(self, sock):
        stop = self._stop

        try:
            while not stop.is_set():
                try:
                    msg = sock.recvmsg()
                except sockio.timeout:
                    continue

                cmd = msg['cmd']
                data = msg.get('data')
                log.debug('cmd: %s%s', cmd, ': ' + repr(data) if data else '')

                if cmd == 'evaluate':
                    if self._is_evaluating:
                        self._code.recv_input(data['source'] + '\n')
                    else:
                        self._code_queue.put(data)
                elif cmd == 'interrupt':
                    self.interrupt()
                elif cmd == 'complete':
                    self.complete(data)
                else:
                    log.error('unknown command: %s', cmd)

        except sockio.error as e:
            log.error('handle_commands error: %s', repr(e))
            stop.set()
