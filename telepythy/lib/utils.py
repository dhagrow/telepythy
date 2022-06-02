import os
import sys
import signal
import threading

from . import logs

BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

DEFAULT_COMMAND = sys.executable
DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 7373
DEFAULT_ADDR = '{}:{}'.format(DEFAULT_HOST, DEFAULT_PORT)

IS_WINDOWS = sys.platform == 'win32'

log = logs.get(__name__)

def get_path(*names):
    return os.path.join(BASE_PATH, *names)

def parse_address(address):
    s = address.split(':', 1)
    host = s[0].strip() or DEFAULT_HOST
    if len(s) == 1 or not s[1]:
        return (host, DEFAULT_PORT)
    return (host, int(s[1]))

def start_thread(func, *args, **kwargs):
    def thread(func, *args, **kwargs):
        ident = threading.current_thread().ident
        func_name = getattr(func, '__qualname__', func.__name__)

        log.debug('thread started [%s] (%s)', ident, func_name)
        try:
            return func(*args, **kwargs)
        except:
            log.exception('unexpected thread error [%s] (%s)', ident, func_name)
        finally:
            log.debug('thread stopped [%s] (%s)', ident, func_name)

    t = threading.Thread(target=thread, args=(func,) + args, kwargs=kwargs)
    t.daemon = True
    t.start()
    return t

# if IS_WINDOWS:
#     import ctypes as ct
#     from ctypes import wintypes as wt
#     GenerateConsoleCtrlEvent = ct.windll.kernel32.GenerateConsoleCtrlEvent
#     GenerateConsoleCtrlEvent.argtypes = (wt.DWORD, wt.DWORD)
#     GenerateConsoleCtrlEvent.restype = wt.BOOL

def interrupt(pid=None):
    pid = os.getpid() if pid is None else pid
    log.debug('interrupting process: %s', pid)
    os.kill(pid, signal.CTRL_C_EVENT if IS_WINDOWS else signal.SIGINT)
