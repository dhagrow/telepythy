from __future__ import print_function, unicode_literals

import threading

import prompt_toolkit as pt
from prompt_toolkit.patch_stdout import patch_stdout

import sockio

URL = 'tcp://localhost:6336'
PS1 = '>>> '
PS2 = '... '

class Client(object):
    def __init__(self, address, timeout=None):
        self._client = sockio.connect(address, timeout)

    def evaluate(self, source):
        self._client.sendmsg({'cmd': 'evaluate', 'data': source})
        return self._client.recvmsg()

    def output(self):
        c = self._client
        c.sendmsg({'cmd': 'output'})
        while True:
            yield c.recvmsg()

    def interrupt(self):
        self._client.sendmsg({'cmd': 'interrupt'})

class Repl(object):
    def __init__(self, address):
        self._address = address

        self._session = pt.PromptSession(refresh_interval=0.5)
        self._status = ''

    def repl(self):
        start_thread(self._output)
        client = None

        needs_input = False
        while True:
            try:
                if client is None:
                    client = Client(self._address)
                try:
                    with patch_stdout():
                        source = self._session.prompt(
                            PS2 if needs_input else PS1,
                            bottom_toolbar=lambda: self._status,
                            )

                except KeyboardInterrupt:
                    client.interrupt()
                    needs_input = False
                    print('KeyboardInterrupt')
                    continue
                except EOFError:
                    break

                needs_input = client.evaluate(source)

            except Exception as e:
                client = None
                self._set_disconnected(e)

    def _output(self):
        addr = self._address
        client = None

        while True:
            try:
                if client is None:
                    client = Client(addr, timeout=3)
                for line in client.output():
                    self._set_connected(addr)
                    if line is not None:
                        print(line, end='')
            except Exception as e:
                client = None
                self._set_disconnected(e)

    def _set_connected(self, address):
        msg = '<ansigreen>  </ansigreen> connected: {}:{}'.format(*address)
        self._status = pt.HTML(msg)
        self._session.app.invalidate()

    def _set_disconnected(self, error=None):
        e = error and ': {}'.format(error)
        msg = '<ansired>  </ansired> not connected{}'.format(e)
        self._status = pt.HTML(msg)
        self._session.app.invalidate()

def start_thread(func, *args, **kwargs):
    t = threading.Thread(target=func, args=args, kwargs=kwargs)
    t.daemon = True
    t.start()
    return t

def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-H', '--host', default='localhost')
    parser.add_argument('-P', '--port', required=True)

    args = parser.parse_args()

    Repl((args.host, args.port)).repl()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
