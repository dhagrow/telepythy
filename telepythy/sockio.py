import io
import json
import errno
import socket
import struct
import threading

from . import logs
from .utils import start_thread

BACKLOG = socket.SOMAXCONN
CHUNK_SIZE = io.DEFAULT_BUFFER_SIZE

error = socket.error

log = logs.get(__name__)

def connect(address, timeout=None):
    log.debug('connecting: %s:%s', *address)
    sock = socket.create_connection(address, timeout)
    log.info('connected: %s:%s', *address)
    return SockIO(sock)

def start_server(address, handler, timeout=None, accept_timeout=1, backlog=None):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(accept_timeout)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(address)
    sock.listen(backlog or BACKLOG)

    host, port = sock.getsockname()
    log.info('listening: %s:%s', host, port)

    stop = threading.Event()
    t = start_thread(serve, sock, handler, stop, timeout)
    return (ServerThread(t, stop), (host, port))

def serve(sock, handler, stop, timeout=None):
    while not stop.is_set():
        try:
            s, addr = sock.accept()
        except socket.timeout:
            continue
        s.settimeout(timeout)

        log.info('connected: %s:%s', *addr)
        start_thread(handler, SockIO(s))

class ServerThread(object):
    def __init__(self, thread, stop):
        self._thread = thread
        self._stop = stop

    def stop(self):
        self._stop.set()

    def join(self):
        self._thread.join()

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

class SockIOError(Exception):
    pass

class ReceiveInterrupted(SockIOError):
    pass
