import sys
from logging import *

get = getLogger
log = get(__name__)

def init(debug_level=0, mode=None, log_exceptions=True):
    """Initializes simple logging defaults."""
    root_log = get()

    fmt = '%(levelname).1s %(asctime)s [%(mode)s%(name)s] %(message)s'
    formatter = Formatter(fmt)

    handler = StreamHandler()
    handler.setFormatter(formatter)
    handler.addFilter(ModeFilter(mode))

    root_log.addHandler(handler)
    if   debug_level == 0: level = WARNING
    elif debug_level == 1: level = INFO
    else:                  level = DEBUG
    root_log.setLevel(level)

    if log_exceptions:
        sys.excepthook = handle_exception

    # manage third-party loggers
    get('qdarkstyle').setLevel(WARNING)

def handle_exception(etype, evalue, etb):
    if issubclass(etype, KeyboardInterrupt):
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
