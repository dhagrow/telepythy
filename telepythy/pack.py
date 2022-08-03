#! /usr/bin/env python

import os
import sys
import glob
import zipfile

from .lib import logs

BASE_PATH = os.path.join(os.path.dirname(__file__), '..')

def get_path(*names):
    return os.path.abspath(os.path.join(BASE_PATH, *names))

MAIN = """\
from telepythy.__main__ import main
main()
"""

log = logs.get('telepythy.pack')

def pack():
    # don't run if frozen
    if getattr(sys, 'frozen', False):
        return

    src_path = get_path('telepythy/**/*.py')
    dst_path = get_path('telepythy/telepythy_service.pyz')

    with zipfile.ZipFile(dst_path, 'w', zipfile.ZIP_DEFLATED,
            allowZip64=False) as zip:
        for path in glob.iglob(src_path, recursive=True):
            if 'gui' in path: continue
            dst = os.path.relpath(path)
            log.debug('+ %s', dst)
            zip.write(path, dst)
        zip.writestr('__main__.py', MAIN)

    log.debug('packed lib stored to: %s', dst_path)

    return dst_path

if __name__ == '__main__':
    try:
        logs.init(2, format='%(message)s')
        pack()
    except KeyboardInterrupt:
        pass
