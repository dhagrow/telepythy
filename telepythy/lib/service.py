from __future__ import print_function

import sys
import threading
import traceback
try:
    import queue
except ImportError:
    import Queue as queue

from . import logs
from . import utils
from . import sockio
from . import interpreter
from . import event_handlers

Q_TIMEOUT = 0.1

log = logs.get(__name__)

class Service(object):
    """Base class for client/server services."""
    def __init__(self, locals=None, filename=None, init_shell=False):
        self._timeout = Q_TIMEOUT

        self._thread = None
        self._stop = threading.Event()
        self._shutdown = threading.Event()

        self._events = queue.Queue()
        self._code_queue = queue.Queue()

        self._event_handlers = event_handlers.default_handlers()

        self._is_evaluating = False

        if init_shell:
            # set up a shell environment
            locals = locals or {}
            locals.setdefault('__name__', '__main__')

            sys.argv = ['']
            if not sys.path or sys.path[0] != '':
                sys.path.insert(0, '')

        self._inter = interpreter.Interpreter(locals, filename,
            lambda text: self.add_event('stdout', text=text),
            lambda text: self.add_event('stderr', text=text),
            )

    ## threading ##

    def join(self, timeout=None):
        if self._thread is None:
            raise ServiceError('thread is not running')
        self._thread.join(timeout)
        if self._thread.is_alive():
            raise Timeout()

    ## execution ##

    def run(self):
        shutdown = self._shutdown
        shutdown.clear()

        q = self._code_queue
        timeout = self._timeout

        try:
            while not shutdown.is_set():
                for handler in self._event_handlers:
                    handler()

                try:
                    data = q.get(timeout=timeout)
                except queue.Empty:
                    continue

                self.evaluate(**data)
        finally:
            self._thread = None

    def stop(self):
        self._stop.set()
        self._shutdown.set()

    ## interpreter ##

    @property
    def locals(self):
        return self._inter.locals

    def evaluate(self, source, notify=True):
        self._is_evaluating = True
        with self._inter.hooked():
            try:
                self._inter.evaluate(source)
            except (Exception, KeyboardInterrupt):
                traceback.print_exc()
            finally:
                self._is_evaluating = False
                if notify:
                    self.add_event('done')

    def interrupt(self):
        if self._is_evaluating:
            utils.interrupt()

    def complete(self, prefix):
        matches = self._inter.complete(prefix)
        self.add_event('completion', matches=matches)

    def reset(self):
        self._inter.reset()

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

    def register_event_handler(self, handler):
        self._event_handlers.append(handler)

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
                        self._inter.recv_input(data['source'] + '\n')
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

class Client(Service):
    def start(self, addr):
        if self._thread is not None:
            raise ServiceError('thread already running')
        self._thread = utils.start_thread(self.connect, addr)

    def connect(self, address):
        address = utils.parse_address(address)
        client, _addr = sockio.start_client(address, self._handle)
        try:
            self.run()
        finally:
            client.stop()
            client.join()

class Server(Service):
    def start(self, addr):
        if self._thread is not None:
            raise ServiceError('thread already running')
        self._thread = utils.start_thread(self.serve, addr)

    def serve(self, address):
        address = utils.parse_address(address)
        server, _addr = sockio.start_server(address, self._handle)
        try:
            self.run()
        finally:
            server.stop()
            server.join()

class ServiceError(Exception):
    """Raised for Service errors."""

class Timeout(ServiceError):
    """Raised for join timeouts."""
