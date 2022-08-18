from qtpy import QtCore, QtWidgets

from ..lib import logs

from . import styles
from . import utils

log = logs.get(__name__)

class SettingsWidget(QtWidgets.QWidget):
    def __init__(self, config, window):
        super().__init__(window)

        self._config = config
        self._window = window

        self.setup()

    def setup(self):
        ## styles

        style_box = QtWidgets.QGroupBox('Styles')
        layout = QtWidgets.QFormLayout()
        style_box.setLayout(layout)

        self.theme_combo = combo = QtWidgets.QComboBox()
        combo.addItem('dark')
        combo.addItem('light')
        for style in sorted(QtWidgets.QStyleFactory.keys()):
            combo.addItem(style)
        combo.currentTextChanged.connect(self.to_config)
        layout.addRow('Theme', combo)

        self.syntax_combo = combo = QtWidgets.QComboBox()
        for style in sorted(styles.get_styles()):
            combo.addItem(style)
        combo.currentTextChanged.connect(self.to_config)
        layout.addRow('Syntax', combo)

        font_layout = QtWidgets.QHBoxLayout()
        layout.addRow('Font', font_layout)

        self.font_combo = combo = QtWidgets.QFontComboBox()
        combo.setFontFilters(combo.MonospacedFonts)
        combo.currentFontChanged.connect(self.to_config)
        font_layout.addWidget(combo)

        self.font_size_box = box = QtWidgets.QSpinBox()
        box.setMinimum(1)
        box.valueChanged.connect(self.to_config)
        font_layout.addWidget(box)

        all_font_toggle = QtWidgets.QCheckBox('Show all fonts')
        def state_changed(state):
            flt = (combo.AllFonts
                if state == QtCore.Qt.Checked else combo.MonospacedFonts)
            self.font_combo.clear()
            self.font_combo.setFontFilters(flt)
        all_font_toggle.stateChanged.connect(state_changed)
        layout.addRow('', all_font_toggle)

        ## profiles

        pass

        ##

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(style_box)
        self.setLayout(layout)

    def from_config(self):
        config = self._config

        # styles
        self.set_theme()
        self.set_syntax_style()
        self.set_font()

        window = config.section('window')

        # menus
        view_menu = window['view.menu']
        self._window.menuBar().setVisible(view_menu)
        self._window.action_toggle_menu.setChecked(view_menu)

        self._window.action_toggle_source_title.setChecked(False)

        self._window.resize(*window['size'])

    def to_config(self):
        config = self._config

        style = config.section('style')
        style['theme'] = self.theme_combo.currentText()
        style['syntax'] = self.syntax_combo.currentText()

        font = self.font_combo.currentFont()
        font.setPointSize(self.font_size_box.value())
        style['font'] = font

        self.set_theme()
        self.set_syntax_style()
        self.set_font()

        config.write()

    ## styles ##

    def set_theme(self):
        name = self._config['style.theme']
        app = QtWidgets.QApplication.instance()

        if name in ('dark', 'light'):
            stylesheet = styles.get_theme_stylesheet(name)
        else:
            stylesheet = ''
            if not app.setStyle(name):
                log.error('unknown theme: %s', name)

        app.setStyleSheet(stylesheet)
        self._window.output_edit.highlighter.rehighlight()
        self._window.source_edit.highlighter.rehighlight()

        with utils.block_signals(self.theme_combo):
            self.theme_combo.setCurrentText(name)

    def set_syntax_style(self):
        name = self._config['style.syntax']
        style = styles.get_style(name)

        self._window.output_edit.set_style(style)
        self._window.source_edit.set_style(style)

        with utils.block_signals(self.syntax_combo):
            self.syntax_combo.setCurrentText(name)

    def set_font(self):
        font = self._config['style.font']

        self._window.output_edit.setFont(font)
        self._window.source_edit.setFont(font)

        with utils.block_signals(self.font_combo):
            self.font_combo.setCurrentFont(font)
            self.font_size_box.setValue(font.pointSize())
