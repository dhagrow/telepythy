from __future__ import print_function, unicode_literals

import time
import threading

import sage
import prompt_toolkit as pt

URL = 'tcp://localhost:6336'
PS1 = '>>> '
PS2 = '... '

def main():
    client = sage.Client(URL, retry_count=-1)

    session = pt.PromptSession()
    needs_input = False

    start_thread(output, client)

    while True:
        try:
            source = session.prompt(PS2 if needs_input else PS1)
            needs_input = client.evaluate(source)
            time.sleep(0.01)
        except KeyboardInterrupt:
            client.interrupt()
            needs_input = False
            print('KeyboardInterrupt')
        except EOFError:
            break

def output(client):
    for line in client.output():
        print(line, end='')

def start_thread(func, *args, **kwargs):
    t = threading.Thread(target=func, args=args, kwargs=kwargs)
    t.daemon = True
    t.start()
    return t

if __name__ == '__main__':
    main()
