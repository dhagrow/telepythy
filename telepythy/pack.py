#! /usr/bin/env python

import os
import zipfile

from .lib import logs

BASE_PATH = os.path.join(os.path.dirname(__file__), '..')

def get_path(*names):
    return os.path.abspath(os.path.join(BASE_PATH, *names))

MAIN = """\
from lib import __main__
__main__.main()
"""

log = logs.get(__name__)

def pack(force=False):
    src_path = get_path('telepythy', 'lib')
    dst_path = get_path('telepythy.pyz')

    if os.path.exists(dst_path) and not force:
        return

    with zipfile.PyZipFile(dst_path, 'w', optimize=2) as zip:
        zip.writepy(src_path)
        zip.writestr('__main__.py', MAIN)

    log.debug('packed lib stored to: %s', dst_path)

    return dst_path

if __name__ == '__main__':
    try:
        path = pack()
        print('saved to:', path)
    except KeyboardInterrupt:
        pass
