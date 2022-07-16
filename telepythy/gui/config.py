import os

import appdirs
import snekcfg
from qtpy import QtGui, QtWidgets

from ..lib import logs
from ..lib import utils

log = logs.get(__name__)

def get_config_path(*names):
    cfg_dir = appdirs.user_config_dir('telepythy', False)
    return os.path.join(cfg_dir, *names)

def get_config_file_path():
    return get_config_path('telepythy.cfg')

def expand_path(path):
    return os.path.expanduser(os.path.expandvars(path))

def init(path=None):
    path = expand_path(path or get_config_file_path())

    os.makedirs(os.path.dirname(path), exist_ok=True)
    log.debug('config: %s', path)

    cfg = snekcfg.Config(path)
    register_types(cfg)

    cfg.register_type('path', None, expand_path)

    sct = cfg.section('profiles', create=True)
    sct.init('default.command', utils.DEFAULT_COMMAND)
    sct.init('connect.connect', utils.DEFAULT_ADDR)
    sct.init('serve.serve', utils.DEFAULT_ADDR)

    cfg.init('startup.source_path', get_config_path('startup.py'), 'path')

    sct = cfg.section('style', create=True)
    sct.init('app', 'dark')
    sct.init('highlight', 'gruvbox-dark')
    sct.init('font', QtGui.QFont('monospace', 12))

    sct = cfg.section('window', create=True)

    size = QtWidgets.QApplication.primaryScreen().availableSize()
    default_size = (int(size.width() / 2.5), int(size.height() / 1.5))
    sct.init('size', default_size, 'tuple[int, ...]')

    sct.init('view.menu', True)

    cfg.sync()

    return cfg

def register_types(cfg):
    def str2font(v):
        family, size = v.split(',')
        return QtGui.QFont(family.strip(), int(size.strip()))
    cfg.register_type(QtGui.QFont,
        lambda v: f'{v.family()},{v.pointSize()}',
        str2font,
        )
