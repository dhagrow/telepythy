import time
import signal
import itertools

from telepythy import connect
from telepythy import logs

logs.init(2)

def handler(signum, frame):
    connect(('localhost', 7357), locals())

signal.signal(signal.SIGUSR1, handler)

for i in itertools.count():
    print('*beep*')
    time.sleep(1)
