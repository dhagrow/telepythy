import faulthandler
faulthandler.enable()

import argparse

from qtpy import QtGui, QtWidgets
import qdarkstyle

from .. import logs
from .. import utils
from .. import control

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

    logs.init(args.verbose, args.quiet, mode='ctl')

    cfg = config.init(args.config)

    # this hacky section ensures that the option that is set passes either a
    # value, or ''
    # the other options will pass None
    ctl = control.get_control(cfg,
        (args.profile or '') if args.profile is not False else None,
        (args.connect or '') if args.connect is not False else None,
        (args.serve or '') if args.serve is not False else None,
        args.verbose, args.quiet)

    app = QtWidgets.QApplication()
    app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='qtpy'))
    app.setWindowIcon(QtGui.QIcon('res/telepathy.svg'))

    win = Window(cfg, ctl)
    win.setWindowTitle('Telepythy')
    win.show()

    try:
        app.exec_()
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('bye!')
