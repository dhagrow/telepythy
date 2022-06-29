import re
import contextlib

from qtpy import QtGui, QtWidgets

rx_indent = re.compile('^[ ]*')

class TextDocument(QtGui.QTextDocument):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDocumentLayout(QtWidgets.QPlainTextDocumentLayout(self))

        self.context = {}

    def blocks(self, start=None, end=None):
        if start is None: start = self.firstBlock()
        if end is None: end = self.lastBlock()
        return BlockIterator(start, end)

    def block_indentation(self, block):
        match = rx_indent.match(block.text())
        return match.end(0) - match.start(0) if match else 0

    @contextlib.contextmanager
    def using_context(self, **kwargs):
        """Temporarily sets additional context for the document.

        This makes it possible to add context that can be used
        by `QSyntaxHighlighter.highlightBlock()`.
        """
        self.context = kwargs
        try:
            yield
        finally:
            self.context = {}

class BlockIterator:
    def __init__(self, start, end):
        self._start = start
        self._end = end

    def __iter__(self):
        block = self._start
        end = self._end
        while block.isValid():
            yield block
            if block == end:
                return
            block = block.next()

    def __reversed__(self):
        block = self._end
        start = self._start
        while block.isValid():
            yield block
            if block == start:
                return
            block = block.previous()
