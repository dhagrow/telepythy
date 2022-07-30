import argparse

from . import logs
from . import utils
from . import client, server

log = logs.get(__name__)

def main():
    parser = argparse.ArgumentParser('telepythy',
        description='This service can run as either an client (-c) or '
            'server (-s).\nThe default is to run as a server.')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('-s', '--serve', nargs='?', default=False,
        help='[default] <interface>:<port> to bind to. '
             'set port to 0 for a random port (default: {})'.format(
            utils.DEFAULT_ADDR))
    group.add_argument('-c', '--connect', nargs='?', default=False,
        help='<host>:<port> to connect to (default: {})'.format(
            utils.DEFAULT_ADDR))

    parser.add_argument('-v', '--verbose', action='count',
        default=0, help='enable verbose output (-vv for more)')

    args = parser.parse_args()

    logs.init(args.verbose, mode='svc')

    # enable reception of ctrl+c events as part of a new console group (win)
    utils.set_console_ctrl_handler()

    # serve unless connect is set
    if args.connect is not False:
        client(address=args.connect, init_shell=True)
    else:
        server(address=args.serve, init_shell=True)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
