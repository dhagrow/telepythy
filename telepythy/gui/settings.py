from qtpy import QtCore, QtWidgets

from . import styles
from . import utils

class SettingsWidget(QtWidgets.QWidget):
    app_style_changed = QtCore.Signal(str)
    highlight_style_changed = QtCore.Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setup()

    def setup(self):
        self.layout = QtWidgets.QFormLayout()
        self.setLayout(self.layout)

        self.app_combo = QtWidgets.QComboBox()
        self.layout.addRow('Application style', self.app_combo)

        self.highlight_combo = QtWidgets.QComboBox()
        self.layout.addRow('Syntax highlight style', self.highlight_combo)

        # add styles
        self.app_combo.addItem('dark')
        self.app_combo.addItem('light')
        for style in sorted(QtWidgets.QStyleFactory.keys()):
            self.app_combo.addItem(style)

        for style in sorted(styles.get_styles()):
            self.highlight_combo.addItem(style)

        self.setup_actions()

    def setup_actions(self):
        self.app_combo.currentTextChanged.connect(self.app_style_changed)
        self.highlight_combo.currentTextChanged.connect(
            self.highlight_style_changed)

    def set_app_style(self, style):
        with utils.block_signals(self.app_combo):
            self.app_combo.setCurrentText(style)

    def set_highlight_style(self, style):
        with utils.block_signals(self.highlight_combo):
            self.highlight_combo.setCurrentText(style)
