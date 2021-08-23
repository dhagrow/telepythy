from qtpy import QtCore, QtWidgets

class InterpreterWidget(QtWidgets.QWidget):
    interpreter_changed = QtCore.Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup()

    def setup(self):
        self.layout = QtWidgets.QFormLayout()
        self.setLayout(self.layout)

        self.python_exec_edit = QtWidgets.QLineEdit()
        self.layout.addRow('Python executable', self.python_exec_edit)

        self.setup_actions()

    def setup_actions(self):
        self.python_exec_edit.textChanged.connect(self.interpreter_changed)

    def set_python_exec(self, path):
        self.python_exec_edit.setText(path)
