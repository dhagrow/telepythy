import re
from qtpy import QtGui, QtWidgets

rx_indent = re.compile('^[ ]*')

class BlockIterator:
    def __init__(self, document, first=None, last=None):
        self.document = document
        self.first = first
        self.last = last

    def __iter__(self):
        last = self.last
        block = self.first or self.document.firstBlock()
        while block.isValid():
            yield block
            if block == last:
                return
            block = block.next()

    def __reversed__(self):
        last = self.last
        block = self.first or self.document.lastBlock()
        while block.isValid():
            yield block
            if block == last:
                return
            block = block.previous()

class TextDocument(QtGui.QTextDocument):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDocumentLayout(QtWidgets.QPlainTextDocumentLayout(self))

    def blocks(self, first=None, last=None):
        return BlockIterator(self, first, last)

    def blockIndentation(self, block):
        match = rx_indent.match(block.text())
        return match.end(0) - match.start(0) if match else 0
