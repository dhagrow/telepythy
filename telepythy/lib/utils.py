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
        ident = threading.current_thread().ident

        log.debug('thread started (%s): %s', ident, func.__name__)
        try:
            return func(*args, **kwargs)
        except:
            log.exception('unexpected thread error')
        finally:
            log.debug('thread stopped (%s): %s', ident, func.__name__)

    t = threading.Thread(target=thread, args=(func,) + args, kwargs=kwargs)
    t.daemon = True
    t.start()
    return t
