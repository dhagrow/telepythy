import re

from pygments.lexers.python import (
    PythonLexer,
    PythonConsoleLexer,
    PythonTracebackLexer,
    line_re,
    )
from pygments.token import Text, Error, Generic, Name, _TokenType
from pygments.lexer import do_insertions

class Lexer(PythonLexer):
    def __init__(self, **options):
        super().__init__(**options)
        self._stack = None

    @property
    def stack(self):
        return self._stack

    @stack.setter
    def stack(self, stack):
        self._stack = stack

    def reset(self):
        self._stack = None

    def get_tokens_unprocessed(self, text):
        """
        Split ``text`` into (tokentype, text) pairs.

        ``stack`` is the initial stack (default: ``['root']``)
        """
        pos = 0
        tokendefs = self._tokens
        statestack = list(self._stack or ('root',))
        statetokens = tokendefs[statestack[-1]]
        while 1:
            for rexmatch, action, new_state in statetokens:
                m = rexmatch(text, pos)
                if m:
                    if action is not None:
                        if type(action) is _TokenType:
                            yield pos, action, m.group()
                        else:
                            yield from action(self, m)
                    pos = m.end()
                    if new_state is not None:
                        # state transition
                        if isinstance(new_state, tuple):
                            for state in new_state:
                                if state == '#pop':
                                    if len(statestack) > 1:
                                        statestack.pop()
                                elif state == '#push':
                                    statestack.append(statestack[-1])
                                else:
                                    statestack.append(state)
                        elif isinstance(new_state, int):
                            # pop, but keep at least one state on the stack
                            # (random code leading to unexpected pops should
                            # not allow exceptions)
                            if abs(new_state) >= len(statestack):
                                del statestack[1:]
                            else:
                                del statestack[new_state:]
                        elif new_state == '#push':
                            statestack.append(statestack[-1])
                        else:
                            assert False, "wrong state def: %r" % new_state
                        statetokens = tokendefs[statestack[-1]]
                    break
            else:
                # We are here only if all state tokens have been considered
                # and there was not a match on any of them.
                try:
                    if text[pos] == '\n':
                        # at EOL, reset state to "root"
                        statestack = ['root']
                        statetokens = tokendefs['root']
                        yield pos, Text, '\n'
                        pos += 1
                        continue
                    yield pos, Error, text[pos]
                    pos += 1
                except IndexError:
                    break

        self._stack = tuple(statestack)

class ConsoleLexer(PythonConsoleLexer):
    def __init__(self, **options):
        super().__init__(**options)
        self._pylexer = Lexer(**options)
        self._tblexer = PythonTracebackLexer(**options)

    def reset(self):
        self._pylexer._stack = None

    def get_tokens_unprocessed(self, text):
        pylexer = self._pylexer
        tblexer = self._tblexer

        curcode = ''
        insertions = []
        curtb = ''
        tbindex = 0
        tb = 0
        for match in line_re.finditer(text):
            line = match.group()
            if line.startswith('>>> ') or line.startswith('... '):
                tb = 0
                insertions.append((len(curcode),
                                   [(0, Generic.Prompt, line[:4])]))
                curcode += line[4:]
            elif line.rstrip() == '...' and not tb:
                # only a new >>> prompt can end an exception block
                # otherwise an ellipsis in place of the traceback frames
                # will be mishandled
                insertions.append((len(curcode),
                                   [(0, Generic.Prompt, '...')]))
                curcode += line[3:]
            else:
                if curcode:
                    yield from do_insertions(
                        insertions,
                        pylexer.get_tokens_unprocessed(curcode))
                    curcode = ''
                    insertions = []
                if (line.startswith('Traceback (most recent call last):') or
                        re.match('  File "[^"]+", line \\d+\\n$', line)):
                    tb = 1
                    curtb = line
                    tbindex = match.start()
                elif line == 'KeyboardInterrupt\n':
                    yield match.start(), Name.Class, line
                elif tb:
                    curtb += line
                    if not (line.startswith(' ') or line.strip() == '...'):
                        tb = 0
                        for i, t, v in tblexer.get_tokens_unprocessed(curtb):
                            yield tbindex+i, t, v
                        curtb = ''
                else:
                    yield match.start(), Generic.Output, line
        if curcode:
            yield from do_insertions(insertions,
                pylexer.get_tokens_unprocessed(curcode))
        if curtb:
            for i, t, v in tblexer.get_tokens_unprocessed(curtb):
                yield tbindex+i, t, v
