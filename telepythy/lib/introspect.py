import os
import ast
import sys
import signal
import pprint
import keyword
import itertools
import linecache
import traceback
import threading
import contextlib
import collections

from . import logs

log = logs.get(__name__)

try:
    range = xrange
except NameError:
    pass

class Code(object):
    def __init__(self, locs=None, filename=None):
        self.locals = locs
        self.filename = filename or 'telepythy'

        self._run_lock = threading.Lock()
        self._last_result = None
        self._result_count = 0
        self._result_limit = 30

        self._block_counter = itertools.count()

        self.init()
        self.reset()

    def init(self):
        sys.stdin = InputIO()
        sys.displayhook = self.displayhook

    def evaluate(self, source):
        block = next(self._block_counter)
        fname = '<{}:{}>'.format(self.filename, block)

        # technique from: https://stackoverflow.com/questions/47183305/file-string-traceback-with-line-preview
        # (size, mtime, lines, fullname)
        linecache.cache[fname] = (
            len(source), None, source.splitlines(True), fname)

        with self.running():
            try:
                mod = compile(source, fname, 'exec', ast.PyCF_ONLY_AST)
                inter = ast.Interactive(mod.body)
                codeob = compile(inter, fname, 'single')

                exec(codeob, self.locals)
            except Exception:
                traceback.print_exc()
            except KeyboardInterrupt:
                traceback.print_exc()

            self._store_result()

    def interrupt(self):
        if self._run_lock.locked():
            os.kill(os.getpid(), signal.SIGINT)
        else:
            log.debug('nothing to interrupt')

    def complete(self, prefix):
        matches = []

        if '.' not in prefix:
            prefix_0 = prefix and prefix[0]

            for kw in keyword.kwlist:
                if kw.startswith(prefix_0):
                    matches.append(kw)

            for name in self.locals.keys():
                if name.startswith(prefix_0):
                    matches.append(name)

            for name in self.locals['__builtins__'].keys():
                if name.startswith(prefix_0):
                    matches.append(name)

        else:
            idents = prefix.split('.')
            parents, prefix = idents[:-1], idents[-1]

            obj = self.locals.get(parents[0])
            if not obj:
                obj = self.locals['__builtins__'].get(parents[0])
                if not obj:
                    return []

            for ident in parents[1:]:
                try:
                    obj = getattr(obj, ident)
                except AttributeError:
                    return []

            prefix_0 = prefix and prefix[0]

            for name in dir(obj):
                if name.startswith(prefix_0):
                    matches.append(name)

        return sorted(matches, key=match_sort_key)

    def _store_result(self):
        if self._last_result is None:
            return

        # pop
        result, self._last_result = self._last_result, None

        self.locals['_'] = result
        self.locals['_{}'.format(self._result_count)] = result

        print('{}: {}'.format(self._result_count, pprint.pformat(result)))

        self._result_count += 1

        # remove old results
        for i in range(max(0, self._result_count-self._result_limit)):
            self.locals.pop('_{}'.format(i), None)

    def recv_input(self, text):
        sys.stdin.write(text)

    def displayhook(self, value):
        self._last_result = value

    @contextlib.contextmanager
    def running(self):
        # ctx = self.locals['__context__']
        with self._run_lock:
            yield
            # ctx.output_mode = 'remote'
            # try:
            #     yield
            # finally:
            #     ctx.output_mode = 'local'

    def reset(self):
        self.locals.clear()
        exec('', self.locals)
        self._result_count = 0

class InputIO:
    def __init__(self):
        self._buffer = collections.deque()
        self._ready = threading.Event()

    def read(self, size):
        buf = self._buffer
        ready = self._ready

        while True:
            if len(buf) < size:
                ready.wait()
                ready.clear()
                continue
            return ''.join(buf.popleft() for _ in range(size))

    def readline(self):
        buf = []
        while True:
            c = self.read(1)
            if c == '\n':
                return ''.join(buf)
            else:
                buf.append(c)

    def write(self, data):
        self._buffer.extend(data)
        self._ready.set()

class OutputIO(object):
    def __init__(self, service, mirror=None):
        self._service = service
        self._mirror = mirror

    def write(self, s):
        if self._mirror is not None:
            self._mirror.write(s)
        if isinstance(s, bytes):
            s = s.decode('utf8')
        self._service.add_event('output', text=s)

    def flush(self):
        if self._mirror is not None:
            self._mirror.flush()

def match_sort_key(match):
    return (match.startswith('_'), match)
