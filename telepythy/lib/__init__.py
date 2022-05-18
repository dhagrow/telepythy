from .service import Service
from . import utils

def connect_thread(locals=None, address=None, init_shell=False):
    """Starts a client in a thread.

    If set, *locals* must be a dictionary specifying the context in which
    code will be executed.

    *address* is used to set the address to connect to (e.g. "localhost:1234").

    If *init_shell* is `True`, then the service interpreter will be initialized
    as if started from a shell. This includes updates to *locals*, `sys.argv`,
    and `sys.path`.

    Returns a `ServiceThread` instance.
    """
    addr = utils.parse_address(address or utils.DEFAULT_ADDR)
    svc = ServiceThread(locals, init_shell=init_shell)
    svc.start_connect(addr)
    return svc

def serve_thread(locals=None, address=None, init_shell=False):
    """Starts a server in a thread.

    *address* is used to set the address to listen on for connections (e.g.
    "localhost:1234").

    If *init_shell* is `True`, then the service interpreter will be initialized
    as if started from a shell. This includes updates to *locals*, `sys.argv`,
    and `sys.path`.

    Returns a `ServiceThread` instance.
    """
    addr = utils.parse_address(address or utils.DEFAULT_ADDR)
    svc = ServiceThread(locals, init_shell=init_shell)
    svc.start_serve(addr)
    return svc

class ServiceThread(Service):
    def __init__(self, locals=None, filename=None, init_shell=False):
        super().__init__(locals, filename, init_shell)
        self._thread = None

    def start_connect(self, addr):
        self._thread = utils.start_thread(self.connect, addr)

    def start_serve(self, addr):
        self._thread = utils.start_thread(self.serve, addr)

    def stop(self):
        self.shutdown()

    def join(self, timeout=None):
        self._thread.join(timeout)
