from PySide2 import QtCore, QtWidgets

from pygments import styles

class StyleWidget(QtWidgets.QWidget):
    output_style_changed = QtCore.Signal(str)
    source_style_changed = QtCore.Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setup()

    def setup(self):
        self.layout = QtWidgets.QFormLayout()
        self.setLayout(self.layout)

        self.output_combo = QtWidgets.QComboBox()
        self.layout.addRow('output style', self.output_combo)

        self.source_combo = QtWidgets.QComboBox()
        self.layout.addRow('source style', self.source_combo)

        for style in sorted(styles.get_all_styles()):
            self.output_combo.addItem(style)
            self.source_combo.addItem(style)

        self.setup_actions()

    def setup_actions(self):
        self.output_combo.currentTextChanged.connect(self.output_style_changed)
        self.source_combo.currentTextChanged.connect(self.source_style_changed)
