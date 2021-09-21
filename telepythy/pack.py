#! /usr/bin/env python

import os
import sys
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
    src_path = get_path('telepythy')
    dst_path = get_path('telepythy.pyz')

    # don't run if frozen
    if getattr(sys, 'frozen', False):
        return

    with zipfile.PyZipFile(dst_path, 'w', optimize=2) as zip:
        zip.writepy(src_path)
        zip.writestr('__main__.py', MAIN)

    log.debug('packed lib stored to: %s', dst_path)

    return dst_path

if __name__ == '__main__':
    try:
        logs.init(2)
        pack()
    except KeyboardInterrupt:
        pass
