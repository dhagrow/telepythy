from __future__ import print_function, unicode_literals

import prompt_toolkit as pt
from prompt_toolkit.patch_stdout import patch_stdout

from . import logs
from . import sockio
from .utils import start_thread

PS1 = '>>> '
PS2 = '... '

log = logs.get(__name__)

class Client(object):
    def __init__(self, address, timeout=None):
        self._client = sockio.connect(address, timeout)

    def evaluate(self, source):
        self._sendcmd('evaluate', source)

    def complete(self, prefix):
        self._sendcmd('complete', prefix)

    def events(self):
        c = self._client
        self._sendcmd('events')
        while True:
            event = c.recvmsg()

            if event:
                name = event['evt']
                if name == 'done':
                    log.debug('evt: done')
                elif name == 'output':
                    log.debug('out: %r', event['data']['text'][:100])
                else:
                    data = event.get('data', '')
                    data = data and ': ' + repr(data)[:100]
                    log.debug('evt: %s%s', event['evt'], data)

            yield event

    def _sendcmd(self, cmd, data=None):
        msg = {'cmd': cmd}
        if data is not None:
            msg['data'] = data
        log.debug('cmd: %s: %s', cmd, data)
        self._client.sendmsg(msg)

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
                for line in client.events():
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
