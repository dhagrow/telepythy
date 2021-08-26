from qtpy import QtCore, QtWidgets
import qdarkstyle

from pygments import styles

class StyleWidget(QtWidgets.QWidget):
    app_style_changed = QtCore.Signal(str)
    output_style_changed = QtCore.Signal(str)
    source_style_changed = QtCore.Signal(str)

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

        self.output_combo = QtWidgets.QComboBox()
        self.layout.addRow('Output highlight style', self.output_combo)

        self.source_combo = QtWidgets.QComboBox()
        self.layout.addRow('Source highlight style', self.source_combo)

        # add styles
        self.app_combo.addItem('qdarkstyle')
        for style in sorted(QtWidgets.QStyleFactory.keys()):
            self.app_combo.addItem(style.lower())

        for style in sorted(styles.get_all_styles()):
            self.output_combo.addItem(style)
            self.source_combo.addItem(style)

        self.setup_actions()

    def setup_actions(self):
        self.app_combo.currentTextChanged.connect(self.set_app_style)
        self.output_combo.currentTextChanged.connect(self.output_style_changed)
        self.source_combo.currentTextChanged.connect(self.source_style_changed)

    def set_app_style(self, style):
        app = QtWidgets.QApplication.instance()
        if style == 'qdarkstyle':
            app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='qtpy'))
        else:
            app.setStyleSheet('')
            app.setStyle(style)

        self.app_combo.setCurrentText(style)

    def set_output_style(self, style):
        self.output_combo.setCurrentText(style)

    def set_source_style(self, style):
        self.source_combo.setCurrentText(style)
