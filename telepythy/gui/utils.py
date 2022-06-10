import os
import sys
import pathlib
import traceback

from qtpy import QtWidgets

from ..lib import logs

log = logs.get(__name__)

APPID = 'dhagrow.telepythy'
if os.path.exists('.git'):
    APPID = '.'.join([APPID, 'dev'])

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
    home_path = pathlib.Path(home_path or pathlib.Path.home())
    venv_path = home_path / '.virtualenvs'

    get_name = lambda p: p.parent.parent.name

    # linux
    for path in venv_path.glob('**/bin/python'):
        yield (get_name(path), str(path))
    # windows
    for path in venv_path.glob('**/Scripts/python.exe'):
        yield (get_name(path), str(path))

if sys.platform == 'win32':
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
