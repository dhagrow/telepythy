from __future__ import print_function, unicode_literals

from gevent import monkey
monkey.patch_all()

import io
import sys
import traceback
import contextlib

import sage
from gevent import queue

URL = 'tcp://localhost:6336'

def main():
    try:
        TeleServer(URL).serve()
    except KeyboardInterrupt:
        pass

class TeleServer(sage.Server):
    def __init__(self, *args, **kwargs):
        super(TeleServer, self).__init__(*args, **kwargs)
        self._output = queue.Queue()
        self._locals = {'__name__': '__remote__', '__doc__': None}

    @sage.command()
    def evaluate(self, source):
        with capture() as (stdout, stderr):
            try:
                exec source in self._locals
            except Exception:
                stderr.write(traceback.format_exc())
        return stdout.getvalue(), stderr.getvalue()

@contextlib.contextmanager
def capture():
    stdout = io.BytesIO()
    stderr = io.BytesIO()
    sys.stdout = stdout
    sys.stderr = stderr
    try:
        yield stdout, stderr
    finally:
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

if __name__ == '__main__':
    main()
