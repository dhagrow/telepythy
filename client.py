from __future__ import print_function, unicode_literals

from gevent import monkey
monkey.patch_all()

import sage
import gevent
import prompt_toolkit as pt

URL = 'tcp://localhost:6336'

def main():
    client = sage.Client(URL)

    session = pt.PromptSession()

    while True:
        try:
            source = session.prompt('>>> ')
            stdout, stderr = client.evaluate(source)
            if stdout: print(stdout, end='')
            if stderr: print(stderr, end='')
        except KeyboardInterrupt:
            # XXX: send to remote end
            print('KeyboardInterrupt')
        except EOFError:
            break

def output(client):
    for line in client.output():
        print(line)

if __name__ == '__main__':
    main()
