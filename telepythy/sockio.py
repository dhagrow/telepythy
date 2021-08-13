import io
import json
import errno
import socket
import struct
import threading

from . import logs

BACKLOG = socket.SOMAXCONN
CHUNK_SIZE = io.DEFAULT_BUFFER_SIZE

log = logs.get(__name__)

def connect(address, timeout=None):
    sock = socket.create_connection(address, timeout)
    return SockIO(sock)

def serve(address, handler, timeout=None, accept_timeout=None, backlog=None):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(accept_timeout)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(address)
    s.listen(backlog or BACKLOG)

    log.info('listening: %s:%s', *s.getsockname())

    while True:
        try:
            sock, addr = s.accept()
        except socket.timeout:
            continue
        sock.settimeout(timeout)

        log.info('connected: %s:%s', *addr)
        start_thread(handler, SockIO(sock))

class SockIO(object):
    def __init__(self, sock, chunk_size=None):
        self._sock = sock
        self._chunk_size = chunk_size or CHUNK_SIZE

    def sendmsg(self, msg):
        data = json.dumps(msg).encode('utf8')
        self.send(data)

    def recvmsg(self):
        data = self.recv()
        if not data:
            raise ReceiveInterrupted()
        return json.loads(data.decode('utf8'))

    def send(self, data):
        data_len = len(data)
        size = struct.pack('>I', data_len)
        self._sock.sendall(size)
        self._sock.sendall(data)

    def recv(self):
        try:
            return b''.join(self.recviter())
        except ReceiveInterrupted:
            return b''

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

    def close(self):
        try:
            self._sock.shutdown(socket.SHUT_RDWR)
        except (OSError, socket.error) as e:
            # ignore if not connected
            if e.errno not in (errno.ENOTCONN,):
                raise
        self._sock.close()

def start_thread(func, *args, **kwargs):
    t = threading.Thread(target=func, args=args, kwargs=kwargs)
    t.daemon = True
    t.start()
    return t

class SockIOError(Exception):
    pass

class ReceiveInterrupted(SockIOError):
    pass
