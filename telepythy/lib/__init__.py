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
    svc = Service(locals, init_shell=init_shell)
    svc.start_connect(address or utils.DEFAULT_ADDR)
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
    svc = Service(locals, init_shell=init_shell)
    svc.start_serve(address or utils.DEFAULT_ADDR)
    return svc
