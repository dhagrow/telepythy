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
        style_layout = QtWidgets.QFormLayout()
        style_box.setLayout(style_layout)

        self.theme_combo = combo = QtWidgets.QComboBox()
        combo.addItem('dark')
        combo.addItem('light')
        for style in sorted(QtWidgets.QStyleFactory.keys()):
            combo.addItem(style)
        combo.currentTextChanged.connect(self.to_config)
        style_layout.addRow('Theme', combo)

        self.syntax_combo = combo = QtWidgets.QComboBox()
        for style in sorted(styles.get_styles()):
            combo.addItem(style)
        combo.currentTextChanged.connect(self.to_config)
        style_layout.addRow('Syntax', combo)

        font_layout = QtWidgets.QHBoxLayout()
        style_layout.addRow('Font', font_layout)

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
        style_layout.addRow('', all_font_toggle)

        ## startup

        startup_box = QtWidgets.QGroupBox('Startup')
        startup_layout = QtWidgets.QFormLayout()
        startup_box.setLayout(startup_layout)

        self.tips_checkbox = box = QtWidgets.QCheckBox()
        box.stateChanged.connect(self.to_config)
        startup_layout.addRow('Show tips', box)

        ## profiles

        pass

        ##

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(style_box)
        layout.addWidget(startup_box)
        self.setLayout(layout)

    def from_config(self):
        config = self._config

        # styles
        self.set_theme()
        self.set_syntax_style()
        self.set_font()

        # startup
        sct = config.section('startup')
        self.tips_checkbox.setChecked(sct['show_tips'])

        # window
        sct = config.section('window')

        view_menu = sct['view.menu']
        self._window.menuBar().setVisible(view_menu)
        self._window.action_toggle_menu.setChecked(view_menu)

        self._window.action_toggle_source_title.setChecked(False)

        self._window.resize(*sct['size'])

    def to_config(self):
        config = self._config

        # styles
        sct = config.section('style')
        sct['theme'] = self.theme_combo.currentText()
        sct['syntax'] = self.syntax_combo.currentText()

        font = self.font_combo.currentFont()
        font.setPointSize(self.font_size_box.value())
        sct['font'] = font

        self.set_theme()
        self.set_syntax_style()
        self.set_font()

        # startup
        sct = config.section('startup')
        sct['show_tips'] = self.tips_checkbox.isChecked()

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
        with utils.block_signals(self.font_size_box):
            self.font_size_box.setValue(font.pointSize())
