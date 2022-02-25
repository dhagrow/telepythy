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
    src_path = get_path('telepythy/**/*.py')
    dst_path = get_path('telepythy.pyz')

    # don't run if frozen
    if getattr(sys, 'frozen', False):
        return

    with zipfile.ZipFile(dst_path, 'w', zipfile.ZIP_DEFLATED,
            allowZip64=False) as zip:
        for path in glob.iglob(src_path, recursive=True):
            if 'gui' in path: continue
            zip.write(path, os.path.relpath(path))
        zip.writestr('__main__.py', MAIN)

    log.debug('packed lib stored to: %s', dst_path)

    return dst_path

if __name__ == '__main__':
    try:
        logs.init(2)
        pack()
    except KeyboardInterrupt:
        pass
