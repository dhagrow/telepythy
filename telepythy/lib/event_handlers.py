import sys

DELAY = 0.1 # seconds

def default_handlers():
    return [handle_pyside6]

def handle_pyside6():
    try:
        QtCore = sys.modules['PySide6'].QtCore
    except (KeyError, AttributeError):
        return

    app = QtCore.QCoreApplication.instance()
    if app is None:
        return

    app.processEvents(QtCore.QEventLoop.AllEvents, int(DELAY * 1000))
    timer = QtCore.QTimer()
    event_loop = QtCore.QEventLoop()
    timer.timeout.connect(event_loop.quit)
    timer.start(int(DELAY * 1000))
    event_loop.exec_()
    timer.stop()
