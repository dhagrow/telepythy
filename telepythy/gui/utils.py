import ctypes
from ctypes import wintypes

def set_app_id():
    appid = 'dhagrow.telepythy'
    res = SetCurrentProcessExplicitAppUserModelID(appid)
    if res != S_OK:
        err = 'SetCurrentProcessExplicitAppUserModelID failed: {:x}'
        raise Exception(err.format(res))

S_OK = 0x0

SetCurrentProcessExplicitAppUserModelID = ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID
SetCurrentProcessExplicitAppUserModelID.argtypes = [wintypes.LPCWSTR]
SetCurrentProcessExplicitAppUserModelID.restype = ctypes.HRESULT
