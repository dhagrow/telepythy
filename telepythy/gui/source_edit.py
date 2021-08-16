import re

from PySide2.QtCore import Qt
from PySide2 import QtCore, QtGui, QtWidgets

from .history import History

_rx_indent = re.compile(r'^(\s*)')

class SourceEdit(QtWidgets.QPlainTextEdit):
    evaluation_requested = QtCore.Signal(str)

    def __init__(self):
        super().__init__()

        self._history = History()
        self._current = None

    def previous(self):
        if not self._history:
            return

        match = self.toPlainText()
        if self._current is None:
            self._current = match

        source = self._history.previous(match)
        if source:
            self.setPlainText(source)
            self.moveCursorPosition(QtGui.QTextCursor.End)

    def next(self):
        if not self._history:
            return

        match = self.toPlainText()
        source = self._history.next(match)
        if source:
            self.setPlainText(source)
        else:
            self.setPlainText(self._current)
        self.moveCursorPosition(QtGui.QTextCursor.End)

    def reset(self):
        self._history.reset()
        self._current = None

    def clear(self):
        self.reset()

        source = self.toPlainText()
        self._history.append(source)

        super().clear()

    ## events ##

    def keyPressEvent(self, event):
        key = event.key()
        mod = event.modifiers()
        ctrl = mod & Qt.ControlModifier

        if key == Qt.Key_Return:
            # only evaluate when all of the following are true:
            # - there is only one line
            # - the text cursor is at the end of the text
            # - the last character is not a space
            # - the last non-space character is not a colon
            # evaluation can be forced by holding control
            cursor = self.textCursor()
            block = cursor.block()
            text = block.text()

            one_line = self.blockCount() == 1
            at_end = cursor.atEnd()
            no_space = text and text[-1] != ' '
            text_s = text.rstrip()
            new_scope = text_s and (text_s[-1] == ':')

            if ctrl or (one_line and at_end and no_space and not new_scope):
                source = self.toPlainText()
                if source:
                    self.evaluation_requested.emit(source)
                return
            else:
                spaces = self.block_indent(block)
                if new_scope:
                    spaces += 4
                self.insertPlainText('\n' + (' ' * spaces))
                return

        elif ctrl and key == Qt.Key_Up:
            self.previous()
            return

        elif ctrl and key == Qt.Key_Down:
            self.next()
            return

        elif key == Qt.Key_Tab:
            self.insertPlainText(' ' * 4)
            return

        elif key == Qt.Key_Backspace:
            cursor = self.textCursor()
            text = cursor.block().text()[:cursor.positionInBlock()]
            if text.startswith(' ') and not text.strip(' '):
                cursor.movePosition(cursor.PreviousCharacter,
                    cursor.KeepAnchor, 4)
                cursor.deleteChar()
                return

        self.reset()

        super().keyPressEvent(event)

    ## utils ##

    def blocks(self, start=None):
        return BlockIterator(start or self.firstVisibleBlock())

    def block_indent(self, block):
        for prev in reversed(self.blocks(block)):
            spaces = _rx_indent.match(prev.text()).group(0)
            if spaces:
                return len(spaces)
        return 0

    def moveCursorPosition(self, position):
        cursor = self.textCursor()
        cursor.movePosition(position)
        self.setTextCursor(cursor)

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
