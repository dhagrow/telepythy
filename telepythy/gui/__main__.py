if __debug__:
    import faulthandler
    faulthandler.enable()

import sys
import signal
import argparse

from qtpy import QtCore, QtGui, QtWidgets

from .. import logs
from .. import control

from . import config
from .window import Window

from .  import resources

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-p', '--profile', default='default',
        help='profile or Python executable to load (default: %(default)s)')
    parser.add_argument('-l', '--list-profiles', action='store_true',
        help='list the configured profiles')

    parser.add_argument('--config', default=config.DEFAULT_PATH,
        help='path to the config file (default: %(default)s)')

    parser.add_argument('-q', '--quiet', action='store_true',
        help='disable all output')
    parser.add_argument('-v', '--verbose', action='count', default=0,
        help='enable verbose output (-vv for more)')

    args = parser.parse_args()

    logs.init(args.verbose, args.quiet, mode='ctl')
    cfg = config.init(args.config)

    if args.list_profiles:
        list_profiles(cfg)
        return

    mgr = control.Manager(cfg, args.verbose, args.quiet)

    app = QtWidgets.QApplication()
    # app.setWindowIcon(QtGui.QIcon(':telepathy'))

    win = Window(cfg, mgr, args.profile)
    win.setWindowTitle('Telepythy')
    win.show()

    # enable clean shutdown on ctrl+c
    setup_int_handler(win)

    sys.exit(app.exec_())

def list_profiles(cfg):
    for name, profile in sorted(cfg.profile.items()):
        print(name, profile)

def setup_int_handler(win):
    signal.signal(signal.SIGINT, get_int_handler(win))
    def timer():
        QtCore.QTimer.singleShot(100, timer)
    timer()

def get_int_handler(win):
    def handler(signum, frame):
        win.close()
    return handler

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('bye!')
