import time
import signal
import itertools

from telepythy.server import serve
from telepythy import logs

logs.init(2)

def handler(signum, frame):
    serve(('0.0.0.0', 5556), locals())

signal.signal(signal.SIGUSR1, handler)

for i in itertools.count():
    print('*beep*')
    time.sleep(1)
