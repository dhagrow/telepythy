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

class Manager(object):
    def __init__(self, config,
            profile=None, connect=None, serve=None, verbose=0, quiet=False):
        """Only one argument should be set. Set an empty string to use defaults."""
        self._config = config
        self._profile = profile
        self._connect = connect
        self._serve = serve
        self._verbose = verbose
        self._quiet = quiet

    def get_control(self, profile=None):
        command = None
        profile = self._profile = profile or self._profile
        connect = self._connect
        serve = self._serve

        if profile is not None or (connect is None and serve is None):
            profile = self._profile or 'default'

            try:
                sec = self._config.section(('interpreter', profile), create=False)
            except KeyError:
                # must be a command
                command = profile
            else:
                command = sec.get('command')
                connect = sec.get('connect')
                serve = sec.get('serve')

        if command is not None:
            ctl = Control(('localhost', 0), command, self._verbose, self._quiet)
            ctl.serve()
            ctl.start()

        elif connect is not None:
            addr = utils.parse_address(self._connect or utils.DEFAULT_ADDR)
            ctl = Control(addr)
            ctl.connect()

        elif serve is not None:
            addr = utils.parse_address(self._serve or utils.DEFAULT_ADDR)
            ctl = Control(addr)
            ctl.serve()
        else:
            assert False, 'invalid control init'

        return ctl

class Control(object):
    def __init__(self, address, command=None, verbose=0, quiet=False, kill_timeout=None):
        self._address = address
        self._command = command
        self._verbose = verbose
        self._quiet = quiet
        self._timeout = TIMEOUT if kill_timeout is None else kill_timeout

        self._server_thread = None
        self._events_thread = None
        self._events_stop = threading.Event()
        self._restart_lock = threading.Lock()

        self._work_socket = None
        self._work_event = threading.Event()
        self._events_socket = None
        self._events_event = threading.Event()

        self._handlers = collections.defaultdict(set)

        self._proc = None

    ## commands ##

    def evaluate(self, source):
        self.get_work_proxy().evaluate(source)

    def complete(self, prefix):
        self.get_work_proxy().complete(prefix)

    ## events ##

    def register(self, event, handler):
        self._handlers[event].add(handler)

    def _events(self, sock):
        stop = self._events_stop
        handle = self._handle_event
        address = self._address

        handle('start')

        proxy = ServiceProxy(sock)

        try:
            for event in proxy.events():
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
            handle('error', e)
            self.restart()

    def _handle_event(self, name, event=None):
        for handler in self._handlers.get(name, []):
            handler(event)

    ## proxies ##

    def get_work_proxy(self):
        self._work_event.wait()
        return ServiceProxy(self._work_socket)

    ## sockets ##

    def serve(self):
        t, host, port = sockio.start_server(self._address, self._set_sockets)
        self._server_thread = t
        # replace in case a port was generated (port=0)
        self._address = (host, port)

    def connect(self):
        def connect(address):
            sock = sockio.connect(address)
            self._set_sockets(sock)

        utils.start_thread(connect, self._address)
        utils.start_thread(connect, self._address)

    def _set_sockets(self, sock):
        if not self._work_socket:
            self._work_socket = sock
            self._work_event.set()
        elif not self._events_socket:
            self._events_thread = utils.start_thread(self._events, sock)
        else:
            assert False, 'third connection'

    ## process management ##

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

    def restart(self):
        with self._restart_lock:
            self.stop()
            self._work_event.clear()
            self._work_socket = None
            self.start()

    def shutdown(self):
        self._events_stop.set()
        self.stop()

class ServiceProxy(object):
    def __init__(self, sock):
        self._sock = sock

    def evaluate(self, source):
        self._sendcmd('evaluate', source)

    def complete(self, prefix):
        self._sendcmd('complete', prefix)

    def events(self):
        c = self._sock
        self._sendcmd('events')
        while True:
            event = c.recvmsg()

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
