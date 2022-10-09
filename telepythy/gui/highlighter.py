# modified from:
# https://github.com/jupyter/qtconsole/blob/master/qtconsole/pygments_highlighter.py
# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import enum

from qtpy import QtGui

from pygments import styles

class BlockState(enum.IntEnum):
    source = 0
    output = 1
    error = 2
    session = 3
    fold = 4

class BlockData(QtGui.QTextBlockUserData):
    """Storage for the user data associated with each line."""
    syntax_stack = ('root',)

    def __init__(self, **kwargs):
        super().__init__()
        self.update(**kwargs)

    @classmethod
    def update_block(cls, block, **kwargs):
        data = block.userData()
        if not data:
            data = cls()
        data.update(**kwargs)
        block.setUserData(data)

    def update(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __repr__(self):
        attrs = ['syntax_stack']
        kwds = ', '.join(['%s=%r' % (attr, getattr(self, attr))
                           for attr in attrs])
        return 'BlockData(%s)' % kwds

class Highlighter(QtGui.QSyntaxHighlighter):
    """Syntax highlighter that uses Pygments for parsing."""

    def __init__(self, lexer, parent):
        super().__init__(parent)

        self._lexer = lexer
        self.set_style(styles.get_style_by_name('default'))

    def reset(self):
        self._lexer.reset()

    def highlightBlock(self, string):
        """Highlight a block of text."""
        if not string:
            return

        doc = self.document()
        block = self.currentBlock()
        data = self.currentBlockUserData()

        state = data and data.state
        if state is None:
            state = doc.context.get('state')

        if state == BlockState.output:
            return
        elif state in (BlockState.session, BlockState.fold):
            style = self._style
            fmt = QtGui.QTextCharFormat()
            fmt.setForeground(QtGui.QBrush(style.highlight_text_color))
            fmt.setBackground(QtGui.QBrush(style.highlight_color))
            self.setFormat(0, block.length(), fmt)

            BlockData.update_block(block, state=state)
            return

        prev_data = block.previous().userData()
        self._lexer.stack = prev_data and prev_data.syntax_stack

        # Lex the text using Pygments
        index = 0
        for token, text in self._lexer.get_tokens(string):
            length = len(text)
            self.setFormat(index, length, self._get_format(token))
            index += length

        BlockData.update_block(block, state=state,
            syntax_stack=self._lexer.stack)

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
