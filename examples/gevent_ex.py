from gevent import monkey
monkey.patch_all()

import time
import random
import itertools

import telepythy
from telepythy.lib import logs

logs.init(2)

server = telepythy.start_server()

for i in itertools.count():
    value = random.random()
    time.sleep(1)
    server.locals.update(locals())
