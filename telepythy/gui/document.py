import re
from qtpy import QtGui, QtWidgets

rx_indent = re.compile('^[ ]*')

class TextDocument(QtGui.QTextDocument):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDocumentLayout(QtWidgets.QPlainTextDocumentLayout(self))

    def blocks(self, start):
        return BlockIterator(start)

    def block_indentation(self, block):
        match = rx_indent.match(block.text())
        return match.end(0) - match.start(0) if match else 0

class BlockIterator:
    def __init__(self, start):
        self._start = start

    def __iter__(self):
        block = self._start
        while block.isValid():
            yield block
            block = block.next()

    def __reversed__(self):
        block = self._start
        while block.isValid():
            yield block
            block = block.previous()
