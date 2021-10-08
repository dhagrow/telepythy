import argparse

from . import logs
from . import utils
from . import connect, serve

log = logs.get(__name__)

def main():
    try:
        _main()
    except KeyboardInterrupt:
        pass

def _main():
    parser = argparse.ArgumentParser('telepythy')

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

    # serve unless connect is set
    if args.connect is not False:
        connect(address=args.connect, embed_mode=False)
    else:
        serve(address=args.serve, embed_mode=False)

if __name__ == '__main__':
    main()
