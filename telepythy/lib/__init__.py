from .service import Client, Server
from . import utils

def client(locals=None, address=None, init_shell=False):
    """Starts a client.

    If set, *locals* must be a dictionary specifying the context in which
    code will be executed.

    *address* is used to set the address to connect to (e.g. "localhost:1234").

    If *init_shell* is `True`, then the service interpreter will be initialized
    as if started from a shell. This includes updates to *locals*, `sys.argv`,
    and `sys.path`.
    """
    svc = Client(locals, init_shell=init_shell)
    svc.connect(address or utils.DEFAULT_ADDR)

def server(locals=None, address=None, init_shell=False):
    """Starts a server.

    *address* is used to set the address to listen on for connections (e.g.
    "localhost:1234").

    If *init_shell* is `True`, then the service interpreter will be initialized
    as if started from a shell. This includes updates to *locals*, `sys.argv`,
    and `sys.path`.
    """
    svc = Server(locals, init_shell=init_shell)
    svc.serve(address or utils.DEFAULT_ADDR)

def start_client(locals=None, address=None, init_shell=False):
    """Starts a client in a thread.

    Arguments are the same as those for `client`.

    Returns a `ServiceThread` instance.
    """
    svc = Client(locals, init_shell=init_shell)
    svc.start(address or utils.DEFAULT_ADDR)
    return svc

def start_server(locals=None, address=None, init_shell=False):
    """Starts a server in a thread.

    Arguments are the same as those for `server`.

    Returns a `ServiceThread` instance.
    """
    svc = Server(locals, init_shell=init_shell)
    svc.start(address or utils.DEFAULT_ADDR)
    return svc
