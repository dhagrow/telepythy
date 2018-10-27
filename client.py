from __future__ import print_function, unicode_literals

import time
import threading

import sage
import prompt_toolkit as pt

URL = 'tcp://localhost:6336'
PS1 = '>>> '
PS2 = '... '

def repl(client):
    session = pt.PromptSession()
    needs_input = False

    start_thread(output, client)

    while True:
        try:
            source = session.prompt(PS2 if needs_input else PS1)
            needs_input, stdout, stderr = client.evaluate(source)
            if stdout: print(stdout, end='')
            if stderr: print(stderr, end='')
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

def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--url', default=URL,
        help='the server bind URL (default=%(default)s)')

    args = parser.parse_args()
    client = sage.Client(args.url, retry_count=-1)
    repl(client)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
