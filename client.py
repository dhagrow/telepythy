from __future__ import print_function, unicode_literals

from gevent import monkey
monkey.patch_all()

import seer
import gevent
from prompt_toolkit import prompt

URL = 'tcp://localhost:6336'

def main():
    client = seer.Client(URL)
    # gevent.spawn(output, client)

    while True:
        try:
            source = prompt('>>> ')
            stdout, stderr = client.evaluate(source)
            print(repr(stdout))
            print(repr(stderr))
        except KeyboardInterrupt:
            print('KeyboardInterrupt')
        except EOFError:
            break

def output(client):
    for line in client.output():
        print(line)

if __name__ == '__main__':
    main()
