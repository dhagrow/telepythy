from gevent import monkey
monkey.patch_all()

import time
import random
import itertools

import gevent

import telepythy
from telepythy.lib import logs

logs.init(2)

svc = telepythy.Service(globals())
gevent.spawn(svc.serve)

for i in itertools.count():
    value = random.random()
    time.sleep(1)
    svc.locals.update(locals())
