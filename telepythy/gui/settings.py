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

        self.app_combo = combo = QtWidgets.QComboBox()
        combo.addItem('dark')
        combo.addItem('light')
        for style in sorted(QtWidgets.QStyleFactory.keys()):
            combo.addItem(style)
        combo.currentTextChanged.connect(self.to_config)
        layout.addRow('Application style', combo)

        self.highlight_combo = combo = QtWidgets.QComboBox()
        for style in sorted(styles.get_styles()):
            combo.addItem(style)
        combo.currentTextChanged.connect(self.to_config)
        layout.addRow('Syntax highlight style', combo)

        self.font_combo = combo = QtWidgets.QFontComboBox()
        combo.setFontFilters(combo.MonospacedFonts)
        combo.currentFontChanged.connect(self.to_config)
        layout.addRow('Font', combo)

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
        self.set_app_style()
        self.set_highlight_style()
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
        style['app'] = self.app_combo.currentText()
        style['highlight'] = self.highlight_combo.currentText()
        style['font'] = self.font_combo.currentFont()

        self.set_app_style()
        self.set_highlight_style()
        self.set_font()

        config.write()

    ## styles ##

    def set_app_style(self):
        name = self._config['style.app']
        app = QtWidgets.QApplication.instance()

        if name in ('dark', 'light'):
            stylesheet = styles.get_app_stylesheet(name)
        else:
            stylesheet = ''
            if not app.setStyle(name):
                log.error('unknown app style: %s', name)

        app.setStyleSheet(stylesheet)
        self._window.output_edit.highlighter.rehighlight()
        self._window.source_edit.highlighter.rehighlight()

        with utils.block_signals(self.app_combo):
            self.app_combo.setCurrentText(name)

    def set_highlight_style(self):
        name = self._config['style.highlight']
        style = styles.get_style(name)

        self._window.output_edit.set_style(style)
        self._window.source_edit.set_style(style)

        with utils.block_signals(self.highlight_combo):
            self.highlight_combo.setCurrentText(name)

    def set_font(self):
        font = self._config['style.font']

        self._window.output_edit.setFont(font)
        self._window.source_edit.setFont(font)

        with utils.block_signals(self.font_combo):
            self.font_combo.setCurrentFont(font)
