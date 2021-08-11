import sys
from logging import *

get = getLogger
log = get(__name__)

def init(debug_level=0, log_exceptions=True):
    """Initializes simple logging defaults."""
    root_log = get()

    # init only once
    if root_log.handlers: return

    fmt = '%(levelname).1s %(asctime)s . %(message)s'
    formatter = Formatter(fmt)

    handler = StreamHandler()
    handler.setFormatter(formatter)

    root_log.addHandler(handler)
    root_log.setLevel(DEBUG if debug_level > 0 else INFO)

    if log_exceptions:
        sys.excepthook = handle_exception

def handle_exception(etype, evalue, etb):
    if issubclass(etype, KeyboardInterrupt):
        sys.__excepthook__(etype, evalue, etb)
        return
    log.error('unhandled exception', exc_info=(etype, evalue, etb))
