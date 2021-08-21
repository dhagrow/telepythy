import threading

from . import logs

DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 7357
DEFAULT_ADDR = '{}:{}'.format(DEFAULT_HOST, DEFAULT_PORT)

log = logs.get(__name__)

def parse_address(address):
    s = address.split(':', 1)
    host = s[0].strip() or DEFAULT_HOST
    if len(s) == 1 or not s[1]:
        return (host, DEFAULT_PORT)
    return (host, int(s[1]))

def start_thread(func, *args, **kwargs):
    def thread(func, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            log.exception('unexpected thread error')

    t = threading.Thread(target=thread, args=(func,) + args, kwargs=kwargs)
    t.daemon = True
    t.start()
    return t
