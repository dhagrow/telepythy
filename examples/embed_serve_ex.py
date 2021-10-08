import time
import random
import itertools

import telepythy
from telepythy.lib import logs

logs.init(2)

svc = telepythy.serve_thread()

for i in itertools.count():
    value = random.random()
    time.sleep(1)
    svc.locals.update(locals())
