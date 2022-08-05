import time
import random
import itertools

import telepythy
from telepythy.lib import logs

logs.init(verbose=2)

server = telepythy.start_server()

for i in itertools.count():
    value = random.random()
    time.sleep(1)
    server.locals.update(locals())

    print(i)
