import sys
import signal
import argparse

# absolute imports to support PyInstaller
# https://github.com/pyinstaller/pyinstaller/issues/2560
from PySide6 import QtCore, QtGui, QtWidgets

from telepythy import pack
from telepythy.lib import logs

from telepythy.gui.window import Window
from telepythy.gui import resources # import ensures availability
from telepythy.gui import config
from telepythy.gui import utils

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-p', '--profile', default='default',
        help='profile or Python executable to load (default: %(default)s)')
    parser.add_argument('-l', '--list-profiles', action='store_true',
        help='list the configured profiles')

    parser.add_argument('--config', default=config.get_config_file_path(),
        help='path to the config file (default: %(default)s)')

    parser.add_argument('-v', '--verbose', action='count', default=0,
        help='enable verbose output (-vv for more)')

    # undocumented support for self-debugging
    parser.add_argument('-d', '--debug', action='store_true',
        help=argparse.SUPPRESS)

    args = parser.parse_args()

    app = QtWidgets.QApplication()
    app.setWindowIcon(QtGui.QIcon(':icon'))

    logs.init(args.verbose, mode='ctl', color=True, log_exceptions=True)
    cfg = config.init(args.config)

    if args.debug:
        pack.pack()

    if args.list_profiles:
        list_profiles(cfg)
        return

    utils.set_app_id()
    utils.hook_exceptions()

    win = Window(cfg, args.profile, args.verbose, args.debug)
    win.setWindowTitle('Telepythy')
    win.show()

    # enable clean shutdown on ctrl+c
    setup_int_handler(win)

    sys.exit(app.exec())

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
