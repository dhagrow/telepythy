#! /usr/bin/env python

import os
import sys
import glob
import zipfile
import argparse

from .lib import logs

BASE_PATH = os.path.join(os.path.dirname(__file__), '..')

def get_path(*names):
    return os.path.abspath(os.path.join(BASE_PATH, *names))

MAIN = """\
from telepythy.__main__ import run
run()
"""

log = logs.get('telepythy.pack')

def pack(dst_path=None):
    # don't run if frozen
    if getattr(sys, 'frozen', False):
        return

    src_path = get_path('telepythy/**/*.py')

    with zipfile.ZipFile(dst_path, 'w', zipfile.ZIP_DEFLATED,
            allowZip64=False) as zip:
        for path in glob.iglob(src_path, recursive=True):
            if 'gui' in path: continue
            dst = os.path.relpath(path)
            log.debug('+ %s', dst)
            zip.write(path, dst)
        zip.writestr('__main__.py', MAIN)

    log.info('packed lib stored to: %s', dst_path)

    return dst_path

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-o', '--output-path',
        default=get_path('telepythy/telepythy_service.pyz'),
        help='path for the service package (default: %(default)s)')

    parser.add_argument('-v', '--verbose', action='count', default=0,
        help='enable verbose output (-vv for more)')

    args = parser.parse_args()

    logs.init(args.verbose, format='%(message)s')

    pack(args.output_path)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
