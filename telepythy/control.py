import time
import shlex
import threading
import subprocess
import collections

from . import logs
from . import utils
from . import sockio

MODULE = 'telepythy'
TIMEOUT = 5

log = logs.get(__name__)

class Manager:
    def __init__(self, config, verbose=0, quiet=False):
        self._config = config
        self._verbose = verbose
        self._quiet = quiet

    def get_control(self, profile=None, connect=None, serve=None):
        command = None

        if profile is not None or (connect is None and serve is None):
            profile = profile or 'default'

            try:
                sec = self._config.profile[profile]
            except KeyError:
                # must be a command
                command = profile
            else:
                command = sec.get('command')
                connect = sec.get('connect')
                serve = sec.get('serve')

        if command is not None:
            return ProcessControl(('localhost', 0), command,
                self._verbose, self._quiet)

        elif connect is not None:
            addr = utils.parse_address(connect or utils.DEFAULT_ADDR)
            return ClientControl(addr)

        elif serve is not None:
            addr = utils.parse_address(serve or utils.DEFAULT_ADDR)
            return ServerControl(addr)

        assert False, 'invalid control init'

class Control(object):
    def __init__(self, address):
        self._address = address

        self._handlers = collections.defaultdict(set)

        self._work_socket = None
        self._work_event = threading.Event()
        self._events_thread = None
        self._events_stop = threading.Event()

        self._restart_lock = threading.Lock()

    def init(self):
        raise NotImplementedError('abstract')

    ## commands ##

    def evaluate(self, source, notify=True):
        self.get_work_proxy().evaluate(source, notify)

    def interrupt(self):
        self.get_work_proxy().interrupt()

    def complete(self, prefix):
        self.get_work_proxy().complete(prefix)

    ## events ##

    def register(self, event, handler):
        self._handlers[event].add(handler)

    def _events(self, sock):
        stop = self._events_stop
        stop.clear()

        handle = self._handle_event
        address = self._address

        proxy = ServiceProxy(sock)

        try:
            for event in proxy.events(stop):
                if stop.is_set():
                    break
                if event is None:
                    handle(None, address)
                    continue
                name = event['evt']
                handle(name, event)
        except Exception as e:
            if stop.is_set():
                return
            handle('error', repr(e))
            self.restart()

    def _handle_event(self, name, event=None):
        for handler in self._handlers.get(name, []):
            handler(event)

    ## proxies ##

    def get_work_proxy(self):
        if not self._work_socket:
            raise Exception('no connection')
        return ServiceProxy(self._work_socket)

    ## sockets ##

    def _set_sockets(self, sock):
        self._work_socket = sock
        self._work_event.set()
        self._events_thread = utils.start_thread(self._events, sock)

    def restart(self):
        with self._restart_lock:
            log.debug('restarting')
            self._restart()

    def _restart(self):
        self._work_event.clear()
        self._work_socket = None
        self._events_stop.set()
        self._events_thread = None

    def shutdown(self):
        self._events_stop.set()

class ClientControl(Control):
    def __init__(self, address):
        super().__init__(address)
        self._connect_stop = threading.Event()

    def init(self):
        self.connect()

    def connect(self):
        stop = self._connect_stop

        def connect(address):
            while not stop.is_set():
                try:
                    sock = sockio.connect(address)
                except sockio.error as e:
                    log.debug('connection failed: %s', e)
                    time.sleep(1)
                    continue
                else:
                    self._set_sockets(sock)
                    break

        utils.start_thread(connect, self._address)

    def _restart(self):
        super()._restart()
        self.connect()

    def shutdown(self):
        super().shutdown()
        self._connect_stop.set()

class ServerControl(Control):
    def __init__(self, address):
        super().__init__(address)
        self._server_thread = None

    def init(self):
        self.serve()

    def serve(self):
        # replace address in case a port was generated (port=0)
        self._server_thread, self._address = sockio.start_server(
            self._address, self._set_sockets)

    def shutdown(self):
        if self._server_thread:
            self._server_thread.stop()
        super().shutdown()

class ProcessControl(ServerControl):
    def __init__(self, address, command=None, verbose=0, quiet=False, kill_timeout=None):
        super().__init__(address)

        self._proc = None

        self._command = command
        self._verbose = verbose
        self._quiet = quiet
        self._timeout = TIMEOUT if kill_timeout is None else kill_timeout

    def init(self):
        self.serve()
        self.start()

    def start(self):
        if self._proc:
            return

        cmd = shlex.split(self._command) + ['-m', MODULE]
        if not self._quiet:
            cmd.extend(['-v'] * self._verbose)
        cmd.extend(['-c', '{}:{}'.format(*self._address)])

        log.debug('starting process: %s', cmd)
        self._proc = subprocess.Popen(cmd)

    def stop(self):
        proc = self._proc
        if not proc:
            return
        log.debug('stopping process')

        proc.terminate()
        try:
            proc.wait(self._timeout)
        except subprocess.TimeoutExpired:
            log.warning('terminate timed out. killing ...')
            proc.kill()
        proc.wait()

        self._proc = None

    def _restart(self):
        self.stop()
        super()._restart()
        self.start()

    def shutdown(self):
        super().shutdown()
        self.stop()

class ServiceProxy(object):
    def __init__(self, sock):
        self._sock = sock

    def evaluate(self, source, notify=True):
        self._sendcmd('evaluate', {'source': source, 'notify': notify})

    def interrupt(self):
        self._sendcmd('interrupt')

    def complete(self, prefix):
        self._sendcmd('complete', prefix)

    def events(self, stop):
        sock = self._sock

        while not stop.is_set():
            event = sock.recvmsg()

            if event:
                name = event['evt']
                if name == 'done':
                    log.debug('evt: done')
                elif name == 'output':
                    log.debug('out: %r', event['data']['text'][:100])
                else:
                    data = event.get('data', '')
                    data = data and ': ' + repr(data)[:100]
                    log.debug('evt: %s%s', event['evt'], data)

            yield event

    def _sendcmd(self, cmd, data=None):
        msg = {'cmd': cmd}
        if data is not None:
            msg['data'] = data
        data = (data or '') and ': ' + repr(data)
        log.debug('cmd: %s%s', cmd, data)
        self._sock.sendmsg(msg)
