import argparse

from . import logs
from . import utils
from . import sockio
from . import service

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

    args = parser.parse_args()

    logs.init(args.verbose, mode='svc', log_exceptions=False)

    # serve unless connect is set
    if args.connect is not False:
        connect(utils.parse_address(args.connect or utils.DEFAULT_ADDR))
    else:
        serve(utils.parse_address(args.serve or utils.DEFAULT_ADDR))

def connect(address, locs=None, output_mode=None):
    svc = service.Service(locs, output_mode)

    def _connect(svc, address):
        svc.handle(sockio.connect(address))

    threads = []
    t = utils.start_thread(_connect, svc, address)
    threads.append(t)
    t = utils.start_thread(_connect, svc, address)
    threads.append(t)

    for t in threads:
        t.join()

def serve(address, locs=None, output_mode=None):
    t, _, _ = sockio.start_server(
        address, service.Service(locs, output_mode).handle)
    t.join()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
