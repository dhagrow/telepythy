import argparse

from PySide2 import QtGui, QtWidgets
import qdarkstyle

from .. import logs

from .window import Window

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-H', '--host', default='localhost')
    parser.add_argument('-P', '--port', required=True)

    args = parser.parse_args()

    logs.init(2)
    # manage third-party loggers
    logs.get('qdarkstyle').setLevel(logs.WARNING)

    app = QtWidgets.QApplication()
    app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyside2'))
    app.setWindowIcon(QtGui.QIcon('res/telepathy.svg'))

    win = Window((args.host, args.port))
    win.setWindowTitle('telepythy')
    win.resize(800, 800)
    win.show()

    try:
        app.exec_()
    except KeyboardInterrupt:
        pass
    finally:
        win.stop_events(timeout=1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('bye!')
