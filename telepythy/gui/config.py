import profig
from qtpy import QtCore

DEFAULT_PATH = profig.get_source('telepythy.cfg', 'user')
DEFAULT_INTERPRETER = 'python'

def init(path=None):
    cfg = profig.Config(path or DEFAULT_PATH)

    cfg.init('profile.default.command', DEFAULT_INTERPRETER)

    sec = cfg.section('style')
    sec.init('output', 'gruvbox-dark')
    sec.init('source', 'gruvbox-dark')

    sec = cfg.section('window')
    sec.init('size', QtCore.QSize(800, 800))

    sec = sec.section('view')
    sec.init('menu', True)

    cfg.sync()

    return cfg
