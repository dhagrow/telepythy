# modified from:
# https://github.com/jupyter/qtconsole/blob/master/qtconsole/pygments_highlighter.py
# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from qtpy import QtGui

from pygments import styles
from pygments import lexers

class BlockData(QtGui.QTextBlockUserData):
    """Storage for the user data associated with each line."""
    syntax_stack = ('root',)

    def __init__(self, **kwds):
        for key, value in kwds.items():
            setattr(self, key, value)
        QtGui.QTextBlockUserData.__init__(self)

    def __repr__(self):
        attrs = ['syntax_stack']
        kwds = ', '.join(['%s=%r' % (attr, getattr(self, attr))
                           for attr in attrs])
        return 'BlockData(%s)' % kwds

class Highlighter(QtGui.QSyntaxHighlighter):
    """Syntax highlighter that uses Pygments for parsing."""

    def __init__(self, parent, lexer=None):
        super().__init__(parent)

        self._lexer = lexer or lexers.PythonLexer()
        self._lexer._stack = ('root',)
        self.set_style(styles.get_style_by_name('default'))

    def highlightBlock(self, string):
        """Highlight a block of text."""
        prev_data = self.currentBlock().previous().userData()

        if prev_data is not None:
            self._lexer._stack = prev_data.syntax_stack

        # Lex the text using Pygments
        index = 0
        for token, text in self._lexer.get_tokens(string):
            length = len(text)
            self.setFormat(index, length, self._get_format(token))
            index += length

        data = BlockData(syntax_stack=self._lexer._stack)
        self.currentBlock().setUserData(data)

    def set_style(self, style):
        """Sets the style to the specified Pygments style."""
        self._style = style
        self._clear_caches()

        self.rehighlight()

    def _clear_caches(self):
        """Clear caches for brushes and formats."""
        self._brushes = {}
        self._formats = {}

    def _get_format(self, token):
        """Returns a QTextCharFormat for token or `None`."""
        if token in self._formats:
            return self._formats[token]

        result = self._get_format_from_style(token, self._style)

        self._formats[token] = result
        return result

    def _get_format_from_style(self, token, style):
        """Returns a QTextCharFormat for token by reading a Pygments style."""
        result = QtGui.QTextCharFormat()
        for key, value in style.style_for_token(token).items():
            if not value:
                continue
            elif key == 'color':
                result.setForeground(self._get_brush(value))
            elif key == 'bgcolor':
                result.setBackground(self._get_brush(value))
            elif key == 'bold':
                result.setFontWeight(QtGui.QFont.Bold)
            elif key == 'italic':
                result.setFontItalic(True)
            elif key == 'underline':
                result.setUnderlineStyle(
                    QtGui.QTextCharFormat.SingleUnderline)
            elif key == 'sans':
                result.setFontStyleHint(QtGui.QFont.SansSerif)
            elif key == 'roman':
                result.setFontStyleHint(QtGui.QFont.Times)
            elif key == 'mono':
                result.setFontStyleHint(QtGui.QFont.TypeWriter)
        return result

    def _get_brush(self, color):
        """Returns a brush for the color."""
        if color and not color.startswith('#'):
            color = '#' + color
        return QtGui.QBrush(color)

## Monkeypatched lexers to preserve end statestack ##

from pygments.lexer import RegexLexer
from pygments.token import Text, Error, _TokenType

def get_tokens_unprocessed(self, text, stack=('root',)):
    """
    Split ``text`` into (tokentype, text) pairs.

    ``stack`` is the initial stack (default: ``['root']``)
    """
    pos = 0
    tokendefs = self._tokens
    statestack = list(self._stack or stack)
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
RegexLexer._stack = ('root',)
RegexLexer.get_tokens_unprocessed = get_tokens_unprocessed
