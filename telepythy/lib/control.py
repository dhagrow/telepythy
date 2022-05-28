import shlex
import threading
import collections
try:
    import queue
except ImportError:
    import Queue as queue

from . import logs
from . import utils
from . import sockio
from . import killableprocess

TIMEOUT = 0.01
KILL_TIMEOUT = 5

log = logs.get(__name__)

class Control(object):
    def __init__(self, address):
        self._address = address

        self._handlers = collections.defaultdict(set)

        self._cmd_queue = queue.Queue(1)
        self._stop = threading.Event()

    def start(self):
        self._stop.clear()

    def stop(self):
        self._stop.set()

    def restart(self):
        log.debug('restarting')
        self.stop()
        self.start()

    ## commands ##

    def evaluate(self, source, notify=True):
        self._cmd_queue.put(('evaluate', source, notify))

    def interrupt(self):
        self._cmd_queue.put(('interrupt',))

    def complete(self, prefix):
        self._cmd_queue.put(('complete', prefix))

    ## events ##

    def register(self, event, handler):
        self._handlers[event].add(handler)

    ## handlers ##

    def _handle(self, sock):
        self._stop.clear()

        t_evt = utils.start_thread(self._handle_events, sock)
        t_cmd = utils.start_thread(self._handle_commands, sock)

        t_evt.join()
        t_cmd.join()

    def _handle_events(self, sock):
        stop = self._stop
        address = self._address
        call_handlers = self._call_handlers

        try:
            for event in ServiceProxy(sock).events(stop):
                if stop.is_set():
                    break
                if event is None:
                    call_handlers(None, address)
                    continue
                name = event['evt']
                call_handlers(name, event)

        except Exception as e:
            log.debug('_handle_events error: %s', repr(e))
            stop.set()
            call_handlers('error', repr(e))

    def _handle_commands(self, sock):
        stop = self._stop
        q = self._cmd_queue

        try:
            while not stop.is_set():
                try:
                    cmd = q.get(timeout=TIMEOUT)
                except queue.Empty:
                    continue
                cmd_name, *cmd_args = cmd

                func = getattr(ServiceProxy(sock), cmd_name)
                func(*cmd_args)

        except Exception as e:
            log.debug('_handle_commands error: %s', repr(e))
            stop.set()
            self._call_handlers('error', repr(e))

    def _call_handlers(self, name, event=None):
        for handler in self._handlers.get(name, []):
            handler(event)

class ClientControl(Control):
    def __init__(self, address):
        super().__init__(address)
        self._client_thread = None

    def start(self):
        super().start()
        self.connect()

    def stop(self):
        super().stop()
        if self._client_thread:
            self._client_thread.stop()
            self._client_thread.join()
            self._client_thread = None

    def connect(self):
        self._client_thread, _addr = sockio.start_client(
            self._address, self._handle)

class ServerControl(Control):
    def __init__(self, address):
        super().__init__(address)
        self._server_thread = None

    def start(self):
        super().start()
        self.serve()

    def stop(self):
        super().stop()
        if self._server_thread:
            self._server_thread.stop()
            self._server_thread.join()
            self._server_thread = None

    def serve(self):
        # replace address in case a port was generated (port=0)
        self._server_thread, self._address = sockio.start_server(
            self._address, self._handle)

class ProcessControl(ServerControl):
    def __init__(self, address, command, verbose=0, kill_timeout=None):
        super().__init__(address)

        self._proc = None

        self._command = command
        self._verbose = verbose
        self._timeout = KILL_TIMEOUT if kill_timeout is None else kill_timeout

    def start(self):
        super().start()

        lib_path = utils.get_path('telepythy.pyz')

        python = self._command
        cmd = shlex.split(python, posix=False) + [lib_path]
        cmd.extend(['-v'] * self._verbose)
        cmd.extend(['-c', '{}:{}'.format(*self._address)])

        kwargs = {}
        if killableprocess.mswindows:
            kwargs['creationflags'] = killableprocess.winprocess.CREATE_NEW_CONSOLE
            kwargs['startupinfo'] = info = killableprocess.STARTUPINFO()
            info.dwFlags |= killableprocess.STARTF_USESHOWWINDOW

        log.debug('starting process: %s', cmd)
        self._proc = killableprocess.Popen(cmd, **kwargs)

    def stop(self):
        super().stop()

        proc = self._proc
        if not proc:
            log.debug('process not running')
            return

        log.debug('stopping process')

        proc.kill()
        proc.wait(self._timeout)
        self._proc = None

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
            try:
                event = sock.recvmsg()
            except sockio.timeout:
                continue

            if event:
                name = event['evt']
                if name == 'done':
                    log.debug('evt: done')
                elif name == 'stdout':
                    pass
                    # log.debug('out: %r', event['data']['text'][:100])
                elif name == 'stderr':
                    log.debug('err: %r', event['data']['text'][:100])
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
