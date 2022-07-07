import ast
import sys
import pprint
import keyword
import itertools
import linecache
import threading
import contextlib
import collections

try:
    import builtins
except ImportError:
    import __builtin__ as builtins
_builtins = builtins.__dict__

from . import logs

log = logs.get(__name__)

try:
    range = xrange
except NameError:
    pass

class Interpreter(object):
    def __init__(self, locals=None, filename=None,
            stdout_callback=None, stderr_callback=None):

        self.locals = {}
        self._init_locals = locals or {}

        self.filename = filename or 'telepythy'

        self._run_lock = threading.Lock()
        self._result_count = 0
        self._result_limit = 30

        self._block_counter = itertools.count()

        self._last_result = None
        self._stdout_callback = stdout_callback
        self._stderr_callback = stderr_callback

        self.reset()

    def reset(self):
        self.locals.clear()
        exec('', self.locals)
        self.locals.update(self._init_locals)
        self._result_count = 0

    ## commands ##

    def evaluate(self, source):
        block = next(self._block_counter)
        fname = '<{}:{}>'.format(self.filename, block)

        # technique from: https://stackoverflow.com/questions/47183305/file-string-traceback-with-line-preview
        # (size, mtime, lines, fullname)
        linecache.cache[fname] = (
            len(source), None, source.splitlines(True), fname)

        with self._run_lock:
            mod = compile(source, fname, 'exec', ast.PyCF_ONLY_AST)
            inter = ast.Interactive(mod.body)
            codeob = compile(inter, fname, 'single')
            exec(codeob, self.locals)

            self._store_result()

    def complete(self, prefix):
        matches = []
        # log.error('prefix: %s', prefix)

        if '.' not in prefix:
            # return global matches
            for kw in keyword.kwlist:
                matches.append(kw)

            for name in self.locals.keys():
                matches.append(name)

            for name in _builtins.keys():
                matches.append(name)
        else:
            ctx = prefix.rsplit('.', 1)[0]
            try:
                obj = eval(ctx, self.locals)
            except Exception:
                # log.error('ctx failed to resolve: %r', ctx)
                pass
            else:
                # log.error('obj: %s', obj)

                for name in dir(obj):
                    matches.append(name)

        return matches

    def complete_x(self, prefix):
        matches = []

        if '.' not in prefix:
            prefix_0 = prefix and prefix[0]

            for kw in keyword.kwlist:
                if kw.startswith(prefix_0):
                    matches.append(kw)

            for name in self.locals.keys():
                if name.startswith(prefix_0):
                    matches.append(name)

            for name in _builtins.keys():
                if name.startswith(prefix_0):
                    matches.append(name)

        else:
            idents = prefix.split('.')
            parents, prefix = idents[:-1], idents[-1]

            obj = self.locals.get(parents[0])
            if not obj:
                obj = _builtins.get(parents[0])
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

    ## io control ##

    @contextlib.contextmanager
    def hooked(self):
        self.hook()
        try:
            yield
        finally:
            self.unhook()

    def hook(self):
        sys.stdin = InputIO()
        sys.stdout = OutputIO(self._stdout_callback)
        sys.stderr = OutputIO(self._stderr_callback)

        sys.displayhook = self.displayhook

    def unhook(self):
        sys.stdin = sys.__stdin__
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

        sys.displayhook = sys.__displayhook__

    def recv_input(self, text):
        sys.stdin.write(text)

    def displayhook(self, value):
        self._last_result = value

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
    def __init__(self, callback, mirror=None):
        self._callback = callback
        self._mirror = mirror

    def isatty(self):
        # XXX: disabled until support for ANSI codes can be implemented
        return False

    def write(self, s):
        if self._mirror is not None:
            self._mirror.write(s)
        if isinstance(s, bytes):
            s = s.decode('utf8')
        self._callback(s)

    def flush(self):
        if self._mirror is not None:
            self._mirror.flush()

def match_sort_key(match):
    return (match.startswith('_'), match)
