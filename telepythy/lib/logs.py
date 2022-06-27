import sys
from logging import *

iswindows = sys.platform == 'win32'

get = getLogger
log = get(__name__)

def init(verbose=0, mode=None, format=None, color=False, log_exceptions=False):
    """Initializes simple logging defaults."""
    root_log = get('telepythy')
    root_log.propagate = False

    fmt = format or '%(levelname).1s %(asctime)s [%(mode)s%(name)s] %(message)s'

    if verbose == 0:
        handler = NullHandler()
        root_log.addHandler(handler)
        return
    elif sys.stderr is None:
        if not iswindows:
            # TODO: maybe try syslog on linux?
            return
        handler = DbgViewHandler()
        formatter = Formatter(fmt)
    else:
        handler = StreamHandler()
        formatter = Formatter(fmt)

        if color:
            # try to enable color formatting
            try:
                import colorlog
            except ImportError:
                # fail silently. no color
                pass
            else:
                formatter = colorlog.ColoredFormatter('%(log_color)s' + fmt)

    handler.setFormatter(formatter)
    handler.addFilter(ModeFilter(mode))

    root_log.addHandler(handler)
    root_log.setLevel(INFO if verbose == 1 else DEBUG)

    if log_exceptions:
        sys.excepthook = handle_exception

def handle_exception(etype, evalue, etb):
    if not issubclass(etype, Exception):
        # default handling for BaseExceptions
        sys.__excepthook__(etype, evalue, etb)
        return
    log.error('unhandled exception', exc_info=(etype, evalue, etb))

class ModeFilter(Filter):
    def __init__(self, mode):
        super(ModeFilter, self).__init__()
        self._mode = mode + ':' if mode else ''

    def filter(self, record):
        record.mode = self._mode
        return True

class NullHandler(Handler):
    def emit(self, record):
        pass

if iswindows:
    import ctypes as ct
    from ctypes import wintypes as wt

    OutputDebugString = ct.windll.kernel32.OutputDebugStringW
    OutputDebugString.argtypes = [wt.LPCWSTR]
    OutputDebugString.restype = None

    class DbgViewHandler(Handler):
        def emit(self, record):
            OutputDebugString(self.format(record))
