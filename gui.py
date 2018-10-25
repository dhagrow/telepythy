import threading

import sage

from PySide2.QtCore import Qt
from PySide2 import QtCore, QtGui, QtWidgets

URL = 'tcp://localhost:6336'

class Window(QtWidgets.QWidget):
    def __init__(self, url):
        super().__init__()

        self._client = sage.Client(url)
        self.setup()

        start_thread(self._output)

    def setup(self):
        self.action_quit = QtWidgets.QAction()
        self.action_quit.setShortcut(QtGui.QKeySequence.Quit)
        self.action_quit.triggered.connect(self.close)

        self.output_edit = QtWidgets.QPlainTextEdit()
        self.output_edit.setFont(QtGui.QFont('Fira Mono', 12))

        self.source_edit = TextEdit()
        self.source_edit.setFont(QtGui.QFont('Fira Mono', 12))
        self.source_edit.submitted.connect(self._client.evaluate)

        self.splitter = QtWidgets.QSplitter(Qt.Vertical)
        self.splitter.addWidget(self.output_edit)
        self.splitter.addWidget(self.source_edit)
        self.splitter.setStretchFactor(0, 2)

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.splitter)

        self.addAction(self.action_quit)
        self.setLayout(self.layout)

        self.source_edit.setFocus()

    def _output(self):
        for line in self._client.output():
            self.output_edit.insertPlainText(line)

class TextEdit(QtWidgets.QPlainTextEdit):
    submitted = QtCore.Signal(str)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            self.submitted.emit(self.toPlainText())
            self.clear()
        else:
            super().keyPressEvent(event)

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
