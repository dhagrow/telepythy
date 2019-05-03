import re
import threading
import collections

import sage

from PySide2.QtCore import Qt
from PySide2 import QtCore, QtGui, QtWidgets

URL = 'tcp://localhost:6336'
PS1 = '>>> '
PS2 = '... '

_rx_indent = re.compile(r'^(\s*)')

class Window(QtWidgets.QWidget):
    output_received = QtCore.Signal(str)

    def __init__(self, url):
        super().__init__()

        self._client = sage.Client(url)
        self._history_result = collections.OrderedDict()
        self.setup()

        self.append(PS1)

        self.output_received.connect(self.append)
        start_thread(self._output)

    def setup(self):
        self.action_quit = QtWidgets.QAction()
        self.action_quit.setShortcut(QtGui.QKeySequence.Quit)
        self.action_quit.triggered.connect(self.close)

        self.output_edit = QtWidgets.QPlainTextEdit()
        self.output_edit.setFont(QtGui.QFont('Fira Mono', 13))
        self.output_edit.setReadOnly(True)

        self.source_edit = TextEdit(self._client)
        self.source_edit.setFont(QtGui.QFont('Fira Mono', 13))
        self.source_edit.evaluated.connect(self.on_evaluate)

        self.splitter = QtWidgets.QSplitter(Qt.Vertical)
        self.splitter.addWidget(self.output_edit)
        self.splitter.addWidget(self.source_edit)
        self.splitter.setStretchFactor(0, 2)

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.splitter)

        self.addAction(self.action_quit)
        self.setLayout(self.layout)

        self.source_edit.setFocus()

    def on_evaluate(self, source, stdout, stderr):
        self.append(source)
        self.append('\n')
        if stdout: self.append(stdout)
        if stderr: self.append(stderr)
        self.append(PS1)

    def append(self, text):
        self.output_edit.insertPlainText(text)
        scroll = self.output_edit.verticalScrollBar()
        scroll.setValue(scroll.maximum())

    def _output(self):
        for line in self._client.output():
            self.output_received.emit(line)

class TextEdit(QtWidgets.QPlainTextEdit):
    evaluated = QtCore.Signal(str, str, str)

    def __init__(self, client):
        super().__init__()

        self._client = client

        self._index = 0
        self._history = []

    def evaluate(self):
        source = self.toPlainText()

        needs_input, stdout, stderr = self._client.evaluate(source, push=False)
        if needs_input:
            return False
        if '\n' in stderr and stderr.rstrip().rsplit('\n', 1)[1].startswith('SyntaxError'):
            print(stderr)
            return True

        self._index = 0
        if source.strip():
            self._history.append(source)

        self.evaluated.emit(source, stdout, stderr)
        self.clear()

        return True

    def previous(self):
        if not self._history:
            return

        self._index -= 1
        try:
            source = self._history[self._index]
        except IndexError:
            self._index += 1
        else:
            self.setPlainText(source)
            self.moveCursorPosition(QtGui.QTextCursor.End)

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
            # evaluation can be forced by holding control
            cursor = self.textCursor()
            block = cursor.block()
            text = block.text()

            one_line = self.blockCount() == 1
            at_end = cursor.atEnd()
            no_space = text and text[-1] != ' '

            if ctrl or (one_line and at_end and no_space):
                if self.evaluate():
                    return
                else:
                    self.insertPlainText('\n' + (' ' * 4))
                    return
            else:
                spaces = self.block_indent(block)
                self.insertPlainText('\n' + (' ' * spaces))
                return

        elif ctrl and key == Qt.Key_Up:
            self.previous()
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

def start_thread(func, *args, **kwargs):
    t = threading.Thread(target=func, args=args, kwargs=kwargs)
    t.daemon = True
    t.start()
    return t

def main():
    app = QtWidgets.QApplication()

    win = Window(URL)
    win.show()

    app.exec_()

if __name__ == '__main__':
    main()
