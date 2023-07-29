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

        # set to prevent sync loops
        self._reading = False

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
        combo.currentTextChanged.connect(self.sync)
        style_layout.addRow('Theme', combo)

        self.syntax_combo = combo = QtWidgets.QComboBox()
        for style in sorted(styles.get_styles()):
            combo.addItem(style)
        combo.currentTextChanged.connect(self.sync)
        style_layout.addRow('Syntax', combo)

        font_layout = QtWidgets.QHBoxLayout()
        style_layout.addRow('Font', font_layout)

        self.font_combo = combo = QtWidgets.QFontComboBox()
        combo.setFontFilters(combo.FontFilter.MonospacedFonts)
        combo.currentFontChanged.connect(self.sync)
        font_layout.addWidget(combo)

        self.font_size_box = box = QtWidgets.QSpinBox()
        box.setMinimum(1)
        box.valueChanged.connect(self.sync)
        font_layout.addWidget(box)

        all_font_toggle = QtWidgets.QCheckBox('Show all fonts')
        def state_changed(state):
            flt = (combo.FontFilter.AllFonts
                if state == QtCore.Qt.CheckState.Checked.value
                else combo.FontFilter.MonospacedFonts)
            self.font_combo.setFontFilters(flt)
            self.font_combo.view().reset()
        all_font_toggle.stateChanged.connect(state_changed)
        style_layout.addRow('', all_font_toggle)

        ## startup

        startup_box = QtWidgets.QGroupBox('Startup')
        startup_layout = QtWidgets.QFormLayout()
        startup_box.setLayout(startup_layout)

        self.tips_checkbox = box = QtWidgets.QCheckBox()
        box.stateChanged.connect(self.sync)
        startup_layout.addRow('Show tips', box)

        ## profiles

        # TODO

        ##

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(style_box)
        layout.addWidget(startup_box)
        self.setLayout(layout)

    def sync(self):
        if self._reading:
            return
        self.write_config()
        self.read_config()

    def write_config(self):
        cfg = self._config

        # styles
        sct = cfg.section('style')
        sct['theme'] = self.theme_combo.currentText()
        sct['syntax'] = self.syntax_combo.currentText()

        font = self.font_combo.currentFont()
        font.setPointSize(self.font_size_box.value())
        sct['font'] = font

        # startup
        sct = cfg.section('startup')
        sct['show_tips'] = self.tips_checkbox.isChecked()

        cfg.write()

    def read_config(self):
        cfg = self._config
        cfg.read()

        win = self._window

        self._reading = True
        try:
            # theme
            name = cfg['style.theme']
            app = QtWidgets.QApplication.instance()

            if name in ('dark', 'light'):
                stylesheet = styles.get_theme_stylesheet(name)
            else:
                stylesheet = ''
                if not app.setStyle(name):
                    log.error('unknown theme: %s', name)

            app.setStyleSheet(stylesheet)
            win.output_edit.highlighter.rehighlight()
            win.source_edit.highlighter.rehighlight()

            self.theme_combo.setCurrentText(name)

            # syntax
            name = cfg['style.syntax']
            style = styles.get_style(name)

            win.output_edit.set_style(style)
            win.source_edit.set_style(style)

            self.syntax_combo.setCurrentText(name)

            # font
            font = cfg['style.font']

            win.output_edit.setFont(font)
            win.source_edit.setFont(font)

            self.font_combo.setCurrentFont(font)
            self.font_size_box.setValue(font.pointSize())

            # startup
            sct = cfg.section('startup')
            self.tips_checkbox.setChecked(sct['show_tips'])

            # window
            sct = cfg.section('window')

            view_menu = sct['view.menu']
            win.menuBar().setVisible(view_menu)
            win.action_toggle_menu.setChecked(view_menu)

            win.action_toggle_source_title.setChecked(False)

            if not utils.is_i3():
                win.resize(*sct['size'])
        finally:
            self._reading = False
