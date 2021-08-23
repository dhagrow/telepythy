import profig
from qtpy import QtCore

DEFAULT_PATH = profig.get_source('telepythy.cfg', 'user')
DEFAULT_INTERPRETER = 'python'

def init(path=None):
    cfg = profig.Config(path or DEFAULT_PATH)

    cfg.init('interpreter.default.command', DEFAULT_INTERPRETER)

    sec = cfg.section('window')
    sec.init('size', QtCore.QSize(800, 800))

    cfg.sync()

    return cfg
