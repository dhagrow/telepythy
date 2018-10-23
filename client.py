from __future__ import print_function, unicode_literals

from gevent import monkey
monkey.patch_all()

import sage
import gevent
import prompt_toolkit as pt

URL = 'tcp://localhost:6336'
PS1 = '>>> '
PS2 = '... '

def main():
    client = sage.Client(URL, retry_count=-1)

    session = pt.PromptSession()
    needs_input = False

    gevent.spawn(output, client)

    while True:
        try:
            source = session.prompt(PS2 if needs_input else PS1)
            needs_input = client.evaluate(source)
            gevent.sleep(0.1)
        except KeyboardInterrupt:
            print('KeyboardInterrupt')
        except EOFError:
            break

def output(client):
    for line in client.output():
        print(line, end='')

if __name__ == '__main__':
    main()
