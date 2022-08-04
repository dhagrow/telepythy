import sys
from logging import *

iswindows = sys.platform == 'win32'

get = getLogger
log = get(__name__)

def init(verbose=0, mode=None, format=None, color=False, set_excepthook=False):
    """Initializes simple logging defaults."""

    level = {
        0: WARNING,
        1: INFO,
        2: DEBUG,
        }[verbose]

    root_log = get()
    # don't increase the level if it's already been set
    root_log.setLevel(min(level, root_log.level))

    tele_log = get('telepythy')
    # do not propagate logs to parent
    tele_log.propagate = False
    tele_log.setLevel(level)

    fmt = format or '%(levelname).1s %(asctime)s [%(mode)s:%(name)s] %(message)s'

    if sys.stderr is None:
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

    tele_log.addHandler(handler)

    if set_excepthook:
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
        self._mode = mode

    def filter(self, record):
        record.mode = self._mode
        return True

if iswindows:
    import ctypes as ct
    from ctypes import wintypes as wt

    OutputDebugString = ct.windll.kernel32.OutputDebugStringW
    OutputDebugString.argtypes = [wt.LPCWSTR]
    OutputDebugString.restype = None

    class DbgViewHandler(Handler):
        def emit(self, record):
            OutputDebugString(self.format(record))
