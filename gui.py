import sage
from PySide2.QtCore import Qt
from PySide2 import QtCore, QtGui, QtWidgets

URL = 'tcp://localhost:6336'

def execute():
    print('boop')
    c = sage.Client(URL)

    c.evaluate('print(1)')

def main():
    app = QtWidgets.QApplication()

    action_quit = QtWidgets.QAction()
    action_quit.setShortcut(QtGui.QKeySequence.Quit)
    action_quit.triggered.connect(app.quit)

    action_exec = QtWidgets.QAction()
    action_exec.setShortcut(QtGui.QKeySequence(Qt.CTRL, Qt.Key_Enter))
    action_exec.triggered.connect(execute)

    output_edit = QtWidgets.QPlainTextEdit()
    source_edit = QtWidgets.QPlainTextEdit()
    source_edit.addAction(action_exec)

    splitter = QtWidgets.QSplitter(Qt.Vertical)
    splitter.addWidget(output_edit)
    splitter.addWidget(source_edit)
    splitter.setStretchFactor(0, 2)

    layout = QtWidgets.QVBoxLayout()
    layout.addWidget(splitter)

    win = QtWidgets.QWidget()
    win.addAction(action_quit)
    win.setLayout(layout)

    source_edit.setFocus()
    win.show()

    app.exec_()

if __name__ == '__main__':
    main()
