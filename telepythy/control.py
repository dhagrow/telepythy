from . import logs
from . import sockio

log = logs.get(__name__)

class Control(object):
    def __init__(self, sock):
        self._sock = sock

    def evaluate(self, source):
        self._sendcmd('evaluate', source)

    def complete(self, prefix):
        self._sendcmd('complete', prefix)

    def events(self):
        c = self._sock
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
        data = (data or '') and ': ' + repr(data)
        log.debug('cmd: %s%s', cmd, data)
        self._sock.sendmsg(msg)
