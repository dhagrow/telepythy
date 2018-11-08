import time
import threading
import collections

import sage

from PySide2.QtCore import Qt
from PySide2 import QtCore, QtGui, QtWidgets

URL = 'tcp://localhost:6336'
PS1 = '>>> '
PS2 = '... '

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
        self.output_edit.setFont(QtGui.QFont('Fira Mono', 12))
        self.output_edit.setReadOnly(True)

        self.source_edit = TextEdit(self._client)
        self.source_edit.setFont(QtGui.QFont('Fira Mono', 12))
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
        print((needs_input, stdout, stderr))
        if needs_input:
            print('needs input')
            return False

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

        if key == Qt.Key_Return:
            if self.evaluate():
                return
        elif mod & Qt.ControlModifier and key == Qt.Key_Up:
            self.previous()
            return

        super().keyPressEvent(event)

    ## utils ##

    def moveCursorPosition(self, position):
        cursor = self.textCursor()
        cursor.movePosition(position)
        self.setTextCursor(cursor)

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
