import sys
import argparse

from qtpy import QtGui, QtWidgets

from .. import pack
from ..lib import logs

from .window import Window
from .profiles import Profiles
from . import config
from . import utils

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-p', '--profile', default='default',
        help='profile or Python executable to load (default: %(default)s)')
    parser.add_argument('-l', '--list-profiles', action='store_true',
        help='list the configured profiles')

    parser.add_argument('--config', default=config.get_config_file_path(),
        help='path to the config file (default: %(default)s)')

    parser.add_argument('--log-file', help='output logs to the specified file')
    parser.add_argument('-v', '--verbose', action='count', default=0,
        help='enable verbose output (-vv for more)')

    # undocumented support for self-debugging
    parser.add_argument('-d', '--debug', action='store_true',
        help=argparse.SUPPRESS)

    args = parser.parse_args()

    app = QtWidgets.QApplication()
    app.setWindowIcon(QtGui.QIcon(':icon'))

    logs.init(args.verbose, mode='ctl', filename=args.log_file, color=True,
        set_excepthook=True)
    cfg = config.init(args.config)

    if args.debug:
        pack.pack()

    profs = Profiles(cfg.section('profiles'), args.verbose)

    if args.list_profiles:
        list_profiles(profs)
        return

    utils.set_app_id()
    utils.hook_exceptions()

    win = Window(cfg, args.profile, profs, args.debug)
    win.setWindowTitle('Telepythy')
    win.show()

    # enable clean shutdown on ctrl+c
    utils.set_interrupt_handler(win)

    sys.exit(app.exec())

def list_profiles(profs):
    cfg_names = (
        tuple(profs.get_config_profiles()) +
        tuple(profs.get_virtualenv_profiles())
        )
    width = max(len(n.split('.')[0]) for n in cfg_names)

    for name in sorted(cfg_names):
        action, profile = profs.get_profile(name)
        print(f'{name:>{width}} | {action:<7}: {profile}')

def run():
    """This is here for setuptools."""
    try:
        main()
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    run()
