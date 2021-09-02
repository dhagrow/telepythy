import sys
import traceback

from qtpy.QtCore import Qt
from qtpy import QtWidgets

APPID = 'dhagrow.telepythy'

def excepthook(type, value, tb):
    err = ''.join(traceback.format_exception_only(type, value))
    exc = ''.join(traceback.format_exception(type, value, tb))

    box = ErrorBox()
    # box.setStyleSheet("QTextEdit { font-family: monospace; }");
    box.setWindowTitle('Unexpected Exception')
    box.setText(err)

    # hacky as hell, but seems that's what it takes
    txt = box.findChild(QtWidgets.QTextEdit)
    txt.setHtml('<pre>{}</pre>'.format(exc))

    box.exec_()

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

if sys.platform == 'win32':
    import ctypes
    from ctypes import wintypes

    def set_app_id():
        res = SetCurrentProcessExplicitAppUserModelID(APPID)
        if res != S_OK:
            err = 'SetCurrentProcessExplicitAppUserModelID failed: {:x}'
            raise Exception(err.format(res))

    ## definitions ##

    S_OK = 0x0

    SetCurrentProcessExplicitAppUserModelID = ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID
    SetCurrentProcessExplicitAppUserModelID.argtypes = [wintypes.LPCWSTR]
    SetCurrentProcessExplicitAppUserModelID.restype = ctypes.HRESULT

else:
    def set_app_id():
        pass
