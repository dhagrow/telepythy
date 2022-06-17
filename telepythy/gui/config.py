import os

import appdirs
from qtpy import QtWidgets

from . import snekcfg
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

    size = QtWidgets.QApplication.primaryScreen().availableSize()
    default_size = (int(size.width() / 2), int(size.height() / 2))

    cfg = snekcfg.Config()

    cfg.register_type('path', None, expand_path)

    sct = cfg.section('profiles', create=True)
    sct.init('default.command', utils.DEFAULT_COMMAND)
    sct.init('connect.connect', utils.DEFAULT_ADDR)
    sct.init('serve.serve', utils.DEFAULT_ADDR)

    cfg.init('startup.source_path', get_config_path('startup.py'), 'path')

    sct = cfg.section('style', create=True)
    sct.init('app', 'dark')
    sct.init('highlight', 'gruvbox-dark')
    sct.init('font.family', 'monospace')
    sct.init('font.size', 12)

    sct = cfg.section('window', create=True)
    sct.init('size', default_size, tuple[int])
    sct.init('view.menu', True)

    cfg.sync(path)

    return cfg
