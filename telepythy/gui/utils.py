import os
import sys
import glob
import random
import signal
import traceback

import mistune
from qtpy import QtCore, QtWidgets

from ..lib import logs
from ..lib import utils

IS_WINDOWS = sys.platform == 'win32'

log = logs.get(__name__)

APPID = 'dhagrow.telepythy'
if os.path.exists('.git'):
    APPID += '.dev'

def excepthook(type, value, tb):
    err = ''.join(traceback.format_exception_only(type, value))
    exc = ''.join(traceback.format_exception(type, value, tb))

    log.error('unexpected error\n%s', exc)

    box = ErrorBox()
    box.setWindowTitle('Unexpected Exception')
    box.setText(err)

    # hacky as hell, but seems that's what it takes
    txt = box.findChild(QtWidgets.QTextEdit)
    txt.setHtml('<pre>{}</pre>'.format(exc))

    box.exec()

def hook_exceptions():
    sys.excepthook = excepthook

def unhook_exceptions():
    sys.excepthook = sys.__excepthook__

_tips = []
_current_tip = 0
def get_tip(index=None):
    global _current_tip
    if not _tips:
        with open(utils.get_path('docs/tips.txt')) as f:
            car, *cdr = list(filter(None, (line.strip() for line in f)))
            random.shuffle(cdr)
            _tips.append(car)
            _tips.extend(cdr)
    if index is None:
        index = _current_tip % len(_tips)
    _current_tip += 1
    return mistune.html(_tips[index])

class ErrorBox(QtWidgets.QMessageBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDetailedText(' ')

    def resizeEvent(self, event):
        result = super().resizeEvent(event)

        txt = self.findChild(QtWidgets.QTextEdit)
        txt.setFixedSize(txt.sizeHint())

        return result

def virtualenvs(home_path=None):
    home_path = home_path or os.path.expanduser('~')
    venv_path = os.path.join(home_path, '.virtualenvs')

    get_name = lambda p: os.path.basename(os.path.dirname(os.path.dirname(p)))

    # linux
    for path in glob.iglob(os.path.join(venv_path, '**/bin/python')):
        yield (get_name(path), str(path))
    # windows
    for path in glob.iglob(os.path.join(venv_path, '**/Scripts/python.exe')):
        yield (get_name(path), str(path))

def set_interrupt_handler(win):
    signal.signal(signal.SIGINT, get_interrupt_handler(win))
    def timer():
        QtCore.QTimer.singleShot(100, timer)
    timer()

def get_interrupt_handler(win):
    def handler(signum, frame):
        win.close()
    return handler

if IS_WINDOWS:
    import ctypes as ct
    from ctypes import wintypes as wt

    def set_app_id():
        res = SetCurrentProcessExplicitAppUserModelID(APPID)
        if res != S_OK:
            err = 'SetCurrentProcessExplicitAppUserModelID failed: {:x}'
            raise Exception(err.format(res))

    ## constants ##

    S_OK = 0x0

    ## functions ##

    SetCurrentProcessExplicitAppUserModelID = ct.windll.shell32.SetCurrentProcessExplicitAppUserModelID
    SetCurrentProcessExplicitAppUserModelID.argtypes = [wt.LPCWSTR]
    SetCurrentProcessExplicitAppUserModelID.restype = ct.HRESULT

else:
    def set_app_id():
        pass
