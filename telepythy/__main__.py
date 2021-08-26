import argparse

from . import logs
from . import utils
from . import service

log = logs.get(__name__)

def main():
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
    parser.add_argument('-q', '--quiet', action='store_true',
        help='disable all output')

    args = parser.parse_args()

    logs.init(args.verbose, args.quiet, mode='svc', log_exceptions=False)

    svc = service.Service()

    # serve unless connect is set
    if args.connect is not False:
        addr = utils.parse_address(args.connect or utils.DEFAULT_ADDR)
        svc.connect(addr)
    else:
        addr = utils.parse_address(args.serve or utils.DEFAULT_ADDR)
        svc.serve(addr)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
