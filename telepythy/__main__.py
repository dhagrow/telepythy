import argparse

from . import logs
from . import utils
from .server import serve

def main():
    parser = argparse.ArgumentParser('telepythy')
    parser.add_argument('-s', '--serve', default='localhost:7357',
        help='<interface>:<port> to bind the server to. '
             'set port to 0 for a random port (default: %(default)s)')

    args = parser.parse_args()

    logs.init(2, log_exceptions=False)

    serve(utils.parse_address(args.serve))

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
