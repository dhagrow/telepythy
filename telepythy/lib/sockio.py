import io
import json
import time
import errno
import socket
import struct
import threading

from . import logs
from . import utils

TIMEOUT = 0.1
BACKLOG = socket.SOMAXCONN
CHUNK_SIZE = io.DEFAULT_BUFFER_SIZE

error = socket.error
timeout = socket.timeout

log = logs.get(__name__)

def start_client(address, handler, stop=None, retry_limit=-1, retry_interval=1):
    stop = stop or threading.Event()

    t = utils.start_thread(client_loop,
        address, handler, stop, retry_limit, retry_interval)
    return (StoppableThread(t, stop), address)

def client_loop(address, handler, stop, retry_limit, retry_interval):
    count = 0
    timeout = TIMEOUT

    while not stop.is_set():
        try:
            with connect(address, timeout) as sock:
                handler(sock)
        except socket.error as e:
            log.error('connection error: %s', e)

        if stop.is_set():
            break
        count += 1
        if retry_limit != -1 and count > retry_limit:
            log.warning('retry limit reached (attempt #%s)', count)
            break
        time.sleep(retry_interval)
        log.warning('retrying connection (attempt #%s)', count)

def start_server(address, handler, stop=None, backlog=None):
    stop = stop or threading.Event()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(address)
    sock.listen(backlog or BACKLOG)

    host, port = sock.getsockname()
    log.info('listening: %s:%s', host, port)

    t = utils.start_thread(server_loop, sock, handler, stop)
    return (StoppableThread(t, stop), (host, port))

def server_loop(server_sock, handler, stop):
    timeout = TIMEOUT
    server_sock.settimeout(timeout)

    while not stop.is_set():
        try:
            s, addr = server_sock.accept()
        except socket.timeout:
            continue

        log.info('connected: %s:%s', *addr)
        with SockIO(s) as sock:
            sock.settimeout(timeout)
            handler(sock)

def connect(address, timeout=None):
    log.debug('connecting: %s:%s', *address)
    sock = socket.create_connection(address, timeout)
    log.info('connected: %s:%s', *address)
    return SockIO(sock)

class SockIO(object):
    def __init__(self, sock, chunk_size=None):
        self._sock = sock
        self._chunk_size = chunk_size or CHUNK_SIZE

    def sendmsg(self, msg):
        data = json.dumps(msg).encode('utf8')
        self.send(data)

    def recvmsg(self):
        data = self.recv()
        return json.loads(data.decode('utf8'))

    def send(self, data):
        data_len = len(data)
        size = struct.pack('>I', data_len)
        self._sock.sendall(size)
        self._sock.sendall(data)

    def recv(self):
        return b''.join(self.recviter())

    def recviter(self):
        buf = b''.join(self.recvsize(4))
        data_len = struct.unpack('>I', buf)[0]
        for chunk in self.recvsize(data_len):
            yield chunk

    def recvsize(self, size):
        sock = self._sock

        pos = 0
        chunk_size = min(size, self._chunk_size)
        while pos < size:
            chunk = sock.recv(min(size-pos, chunk_size))
            if not chunk:
                raise ReceiveInterrupted()
            pos += len(chunk)
            yield chunk

    def settimeout(self, t):
        self._sock.settimeout(t)

    def close(self):
        try:
            self._sock.shutdown(socket.SHUT_RDWR)
        except (OSError, socket.error) as e:
            # ignore if not connected
            if e.errno not in (errno.ENOTCONN,):
                raise
        self._sock.close()

    def __enter__(self):
        return self

    def __exit__(self, etype, evalue, etb):
        self.close()

class StoppableThread(object):
    def __init__(self, thread, stop):
        self._thread = thread
        self._stop = stop

    def stop(self):
        self._stop.set()

    def join(self):
        self._thread.join()

class SockIOError(Exception):
    pass

class ReceiveInterrupted(SockIOError, error):
    pass
