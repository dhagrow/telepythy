import sys
import argparse

# absolute imports to support PyInstaller
# https://github.com/pyinstaller/pyinstaller/issues/2560
from PySide6 import QtGui, QtWidgets

from telepythy import pack
from telepythy.lib import logs

from telepythy.gui.window import Window
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

    # set default link color to something a little more light/dark friendly
    app = QtWidgets.QApplication.instance()
    pal = app.palette()
    pal.setColor(pal.Link, 'cadetblue')
    app.setPalette(pal)

    win = Window(cfg, args.profile, args.verbose, args.debug)
    win.setWindowTitle('Telepythy')
    win.show()

    # enable clean shutdown on ctrl+c
    utils.set_interrupt_handler(win)

    sys.exit(app.exec())

def list_profiles(cfg):
    items = cfg.section('profiles').items()
    width = max(len(n.split('.')[0]) for n, _ in items)

    for name, profile in sorted(items):
        name, action = name.split('.')
        print(f'{name:>{width}} | {action:<7}: {profile}')

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('bye!')
