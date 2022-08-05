import time
import random
import itertools

import telepythy
from telepythy.lib import logs

logs.init(verbose=2)

client = telepythy.start_client()

for i in itertools.count():
    value = random.random()
    time.sleep(1)
    client.locals.update(locals())

    print(i)
