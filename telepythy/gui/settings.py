from qtpy import QtCore, QtWidgets
import qdarkstyle
from qdarkstyle import utils

from . import palette
from . import styles

class SettingsWidget(QtWidgets.QWidget):
    app_style_changed = QtCore.Signal(str)
    highlight_style_changed = QtCore.Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setup()

    def setup(self):
        self.layout = QtWidgets.QFormLayout()
        self.setLayout(self.layout)

        # workaround: https://github.com/ColinDuquesnoy/QDarkStyleSheet/issues/200
        delegate = QtWidgets.QStyledItemDelegate()
        self.app_combo = QtWidgets.QComboBox()
        self.app_combo.setItemDelegate(delegate)
        self.layout.addRow('Application style', self.app_combo)

        self.highlight_combo = QtWidgets.QComboBox()
        self.layout.addRow('Syntax highlight style', self.highlight_combo)

        # add styles
        self.app_combo.addItem('qdarkstyle')
        for style in sorted(QtWidgets.QStyleFactory.keys()):
            self.app_combo.addItem(style.lower())

        for style in sorted(styles.get_styles()):
            self.highlight_combo.addItem(style)

        self.setup_actions()

    def setup_actions(self):
        self.app_combo.currentTextChanged.connect(self.set_app_style)
        self.highlight_combo.currentTextChanged.connect(self.highlight_style_changed)

    def set_app_style(self, style):
        app = QtWidgets.QApplication.instance()
        if style == 'qdarkstyle':
            pal = palette.TelePalette
            pal.COLOR_BACKGROUND_1 = '#1E1E1E'
            stylesheet = utils.create_qss(pal)
            app.setStyleSheet(stylesheet)
        else:
            app.setStyleSheet('')
            app.setStyle(style)

        self.app_combo.setCurrentText(style)

    def set_highlight_style(self, style):
        self.highlight_combo.setCurrentText(style)
