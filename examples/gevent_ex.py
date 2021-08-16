from gevent import monkey
monkey.patch_all()

import time
print('time.sleep from:', time.sleep.__module__)
import random
import signal

import gevent

from telepythy.server import serve
from telepythy import logs

logs.init(2)

def handler(signum, frame):
    gevent.spawn(serve, ('0.0.0.0', 5556), globals())

signal.signal(signal.SIGUSR1, handler)

def func(a):
    print('start', a)
    time.sleep(random.randint(1, 5))
    print('end', a)

def start():
    for a in 'abcdef':
        gevent.spawn(func, a)

try:
    while True:
        gevent.sleep(1)
except KeyboardInterrupt:
    pass
