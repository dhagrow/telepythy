import shlex
import queue
import subprocess

from . import logs
from . import utils
from . import sockio
from . import control

MODULE = 'telepythy'
TIMEOUT = 5

log = logs.get(__name__)

class Interpreter(object):
    def __init__(self, kill_timeout=None):
        self._timeout = TIMEOUT if kill_timeout is None else kill_timeout

        self._address = None
        self._command = None
        self._proc = None

        self._handlers = queue.Queue()

    def add_handler(self, handler):
        self._handlers.put(handler)

    def handler(self, sock, timeout=None):
        handler = self._handlers.get()
        sock.settimeout(timeout)
        try:
            handler(control.Control(sock))
        except Exception:
            log.exception('process error')
            self.restart()
        finally:
            self._handlers.put(handler)

    def serve(self, address):
        t, host, port = sockio.start_server(address, self.handler)
        self._address = (host, port)

    def connect(self, address):
        def _connect(handler, address):
            handler(sockio.connect(address))

        utils.start_thread(_connect, self.handler, address)
        utils.start_thread(_connect, self.handler, address)

        self._address = address

    def start(self, command=None, verbose=0, quiet=False):
        if self._proc:
            return

        if command:
            cmd = self._command = shlex.split(command) + ['-m', MODULE]
            if not quiet:
                cmd.extend(['-v'] * verbose)
            cmd.extend(['-c', '{}:{}'.format(*self._address)])
        else:
            cmd = self._command

        log.debug('starting process: %s', cmd)
        self._proc = subprocess.Popen(cmd)

    def restart(self):
        if self._proc:
            self.stop()
            self.start()
        else:
            self.start()

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
