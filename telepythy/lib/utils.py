import os
import threading

from . import logs

BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 7357
DEFAULT_ADDR = '{}:{}'.format(DEFAULT_HOST, DEFAULT_PORT)

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

        log.debug('thread started <%s:%s>', func.__qualname__, ident)
        try:
            return func(*args, **kwargs)
        except:
            log.exception('unexpected thread error <%s:%s>', func.__qualname__, ident)
        finally:
            log.debug('thread stopped <%s:%s>', func.__qualname__, ident)

    t = threading.Thread(target=thread, args=(func,) + args, kwargs=kwargs)
    t.daemon = True
    t.start()
    return t
