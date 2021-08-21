import faulthandler
faulthandler.enable()

import argparse

from PySide2 import QtGui, QtWidgets
import qdarkstyle

from .. import logs
from .. import utils
from .. import interpreter

from . import config
from .window import Window

def main():
    parser = argparse.ArgumentParser()

    group = parser.add_mutually_exclusive_group()
    group.add_argument('-s', '--serve', nargs='?', default=False,
        help='<interface>:<port> to bind to. '
             'set port to 0 for a random port (default: {})'.format(
            utils.DEFAULT_ADDR))
    group.add_argument('-c', '--connect', nargs='?', default=False,
        help='<host>:<port> to connect to (default: {})'.format(
            utils.DEFAULT_ADDR))
    group.add_argument('-p', '--profile', nargs='?', default=False,
        help='[default] Python executable or profile to load (default: default)'.format(
            utils.DEFAULT_ADDR))

    parser.add_argument('--config', default=config.DEFAULT_PATH,
        help='path to the config file (default: %(default)s)')
    parser.add_argument('-q', '--quiet', action='store_true',
        help='disable all output')
    parser.add_argument('-v', '--verbose', action='count', default=0,
        help='enable verbose output (-vv for more)')

    args = parser.parse_args()

    if not args.quiet:
        logs.init(args.verbose, mode='ctl')

    cfg = config.init(args.config)

    inter = load_interpreter(args, cfg)

    app = QtWidgets.QApplication()
    app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyside2'))
    app.setWindowIcon(QtGui.QIcon('res/telepathy.svg'))

    win = Window(cfg, inter)
    win.setWindowTitle('telepythy')
    win.show()

    try:
        app.exec_()
    except KeyboardInterrupt:
        pass
    finally:
        inter.stop()

def load_interpreter(args, cfg):
    inter = interpreter.Interpreter()
    if args.connect is not False:
        inter.connect(utils.parse_address(args.connect or utils.DEFAULT_ADDR))

    elif args.serve is not False:
        inter.serve(utils.parse_address(args.serve or utils.DEFAULT_ADDR))

    else:
        inter.serve(utils.parse_address(utils.DEFAULT_ADDR))

        profile = args.profile or 'default'
        sec = cfg.section('interpreter')
        try:
            cmd = sec[profile]
        except KeyError:
            # must be a command
            inter.start(profile, args.verbose, args.quiet)
        else:
            inter.start(cmd, args.verbose, args.quiet)

    return inter

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('bye!')
