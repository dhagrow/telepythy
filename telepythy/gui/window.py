import threading
import collections

from qtpy.QtCore import Qt
from qtpy import QtCore, QtGui, QtWidgets

from pygments.lexers import PythonConsoleLexer

from .. import logs
from .. import control

from .source_edit import SourceEdit
from .output_edit import OutputEdit
from .style_widget import StyleWidget
from .interpreter_widget import InterpreterWidget
from .highlighter import PygmentsHighlighter

log = logs.get(__name__)

class Window(QtWidgets.QMainWindow):
    output_started = QtCore.Signal(str)
    output_stopped = QtCore.Signal()
    output_received = QtCore.Signal(str)
    completion_received = QtCore.Signal(list)
    status_connected = QtCore.Signal(tuple)
    status_disconnected = QtCore.Signal(str)

    def __init__(self, config, control):
        super().__init__()

        self.setup()
        self.config(config)

        self.setup_control(control)

        self._connected = False
        self._history_result = collections.OrderedDict()

        self._set_disconnected(force=True)

    ## config ##

    def config(self, config):
        self._config = config

        # style
        sec = config.style
        self.style_chooser.set_app_style(sec.app)
        self.style_chooser.set_output_style(sec.output)
        self.style_chooser.set_source_style(sec.source)

        # menus
        view_menu = config.window.view.menu
        self.menuBar().setVisible(view_menu)
        self.action_toggle_menu.setChecked(view_menu)

        self.action_toggle_source_title.setChecked(False)

        # profiles
        menu = self.profile_menu
        group = QtWidgets.QActionGroup(menu)
        for name in config.profile:
            action = group.addAction(name)
            action.setCheckable(True)

            if name == 'default':
                action.setChecked(True)

            menu.addAction(action)

        # editors
        sec = config.style
        self.output_highlighter.set_style(sec.output)
        self.source_highlighter.set_style(sec.source)

        # docks
        self.interpreter_chooser.set_python_exec(config.profile.default.command)

        self.resize(*config.window.size)

    ## setup ##

    def setup_control(self, control):
        self._control = ctl = control

        ctl.register(None, lambda address: self.status_connected.emit(address))
        def start(event):
            version = event['data']['version']
            self.output_started.emit(version)
        ctl.register('start', start)
        ctl.register('done', lambda _: self.output_stopped.emit())

        def output(event):
            text = event['data']['text']
            self.output_received.emit(text)
        ctl.register('output', output)

        def completion(event):
            matches = event['data']['matches']
            self.completion_received.emit(matches)
        ctl.register('completion', completion)

        def error(err):
            log.debug('totally normal events error: %s', err)
            self.status_disconnected.emit(err)
        ctl.register('error', error)

        ctl.init()

    def setup(self):
        self.setup_actions()
        self.setup_output_edit()
        self.setup_source_edit()
        self.setup_style_widget()
        self.setup_profile_widget()
        self.setup_menus()
        self.setup_menubar()
        self.setup_statusbar()
        self.setup_signals()

        self.source_edit.setFocus()

    def setup_actions(self):
        self.action_quit = QtWidgets.QAction('Quit')
        self.action_quit.setShortcut('Ctrl+q')
        self.addAction(self.action_quit)

        self.action_restart = QtWidgets.QAction('Restart')
        self.action_restart.setShortcut('Ctrl+F6')
        self.addAction(self.action_restart)

        self.action_clear = QtWidgets.QAction('Clear')
        self.action_clear.setShortcut('Ctrl+l')
        self.addAction(self.action_clear)

        self.action_toggle_menu = QtWidgets.QAction('Menu')
        self.action_toggle_menu.setCheckable(True)
        self.action_toggle_menu.setChecked(True)

        self.action_toggle_source_title = QtWidgets.QAction('Source Title')
        self.action_toggle_source_title.setCheckable(True)
        self.action_toggle_source_title.setChecked(True)

    def setup_output_edit(self):
        self.output_edit = OutputEdit()
        self.output_edit.setFont(QtGui.QFont('Fira Mono', 13))
        self.output_edit.setReadOnly(True)
        self.output_edit.setWordWrapMode(QtGui.QTextOption.WrapAnywhere)

        self.output_highlighter = PygmentsHighlighter(
            self.output_edit.document(), PythonConsoleLexer())

        palette = self.output_edit.palette()
        palette.setColor(QtGui.QPalette.Base, '#333')
        palette.setColor(QtGui.QPalette.Text, Qt.white)
        self.output_edit.setPalette(palette)

        self.setCentralWidget(self.output_edit)

    def setup_source_edit(self):
        self.source_edit = SourceEdit()
        self.source_edit.setFont(QtGui.QFont('Fira Mono', 13))

        self.source_highlighter = PygmentsHighlighter(
            self.source_edit.document())

        palette = self.source_edit.palette()
        palette.setColor(QtGui.QPalette.Base, '#333')
        palette.setColor(QtGui.QPalette.Text, Qt.white)
        self.source_edit.setPalette(palette)

        self.source_dock = QtWidgets.QDockWidget('source')
        self.source_dock.setWidget(self.source_edit)

        self.addDockWidget(Qt.BottomDockWidgetArea, self.source_dock)

    def setup_style_widget(self):
        self.style_chooser = StyleWidget()

        self.style_dock = QtWidgets.QDockWidget('Styles')
        self.style_dock.setWidget(self.style_chooser)
        self.style_dock.setVisible(False)

        self.addDockWidget(Qt.RightDockWidgetArea, self.style_dock)

    def setup_profile_widget(self):
        self.interpreter_chooser = InterpreterWidget()

        self.profile_dock = QtWidgets.QDockWidget('Profiles')
        self.profile_dock.setWidget(self.interpreter_chooser)
        self.profile_dock.setVisible(False)

        self.addDockWidget(Qt.RightDockWidgetArea, self.profile_dock)

    def setup_menus(self):
        self.file_menu = QtWidgets.QMenu('File', self)
        self.file_menu.addAction(self.action_clear)
        self.file_menu.addAction(self.action_restart)
        self.file_menu.addAction(self.action_quit)

        self.view_menu = QtWidgets.QMenu('View', self)
        self.view_menu.addAction(self.action_toggle_menu)
        self.view_menu.addAction(self.style_dock.toggleViewAction())
        self.view_menu.addAction(self.profile_dock.toggleViewAction())
        self.view_menu.addAction(self.action_toggle_source_title)

        self.profile_menu = QtWidgets.QMenu('Profile', self)

        self.status_menu = QtWidgets.QMenu()
        self.status_menu.addMenu(self.file_menu)
        self.status_menu.addMenu(self.view_menu)
        self.status_menu.addMenu(self.profile_menu)

    def setup_menubar(self):
        bar = self.menuBar()
        bar.addMenu(self.file_menu)
        bar.addMenu(self.view_menu)
        bar.addMenu(self.profile_menu)

    def setup_statusbar(self):
        bar = self.statusBar()

        icon = QtGui.QIcon('res/connected.png')
        self._status_pixmap_connected = icon.pixmap(16)
        icon = QtGui.QIcon('res/disconnected.png')
        self._status_pixmap_disconnected = icon.pixmap(16)

        self.menu_button = QtWidgets.QPushButton()
        self.menu_button.setIcon(QtGui.QIcon('res/menu.svg'))
        self.menu_button.setMenu(self.status_menu)
        self.menu_button.setStyleSheet('::menu-indicator{ image: none; }')
        bar.addWidget(self.menu_button)

        self.profile_button = QtWidgets.QPushButton('default')
        self.profile_button.setMenu(self.profile_menu)
        self.profile_button.setStyleSheet('::menu-indicator{ image: none; }')
        bar.addPermanentWidget(self.profile_button)

        self.status_label = QtWidgets.QLabel()
        bar.addPermanentWidget(self.status_label)

        self.status_icon = QtWidgets.QLabel()
        bar.addPermanentWidget(self.status_icon)

    def setup_signals(self):
        self.action_quit.triggered.connect(self.close)
        self.action_restart.triggered.connect(self.restart)
        self.action_clear.triggered.connect(self.clear_output)
        self.action_toggle_menu.toggled.connect(self.menuBar().setVisible)

        def source_toggle(checked):
            w = None if checked else QtWidgets.QWidget(self.source_dock)
            self.source_dock.setTitleBarWidget(w)
        self.action_toggle_source_title.toggled.connect(source_toggle)

        self.profile_menu.triggered.connect(
            lambda action: self.set_profile(action.text()))
        self.profile_menu.triggered.connect(
            lambda action: self.profile_button.setText(action.text()))

        self.source_edit.evaluation_requested.connect(self.evaluate)
        self.source_edit.completion_requested.connect(self.complete)

        self.output_started.connect(self.output_edit.append_session)
        self.output_stopped.connect(self.output_edit.append_prompt)
        self.output_received.connect(self.output_edit.append)

        self.completion_received.connect(self.source_edit.show_completer)

        self.status_connected.connect(self._set_connected)
        self.status_disconnected.connect(self._set_disconnected)

        self.style_chooser.output_style_changed.connect(
            self.output_highlighter.set_style)
        self.style_chooser.source_style_changed.connect(
            self.source_highlighter.set_style)

    ## events ##

    def contextMenuEvent(self, event):
        self.view_menu.exec_(event.globalPos())

    def closeEvent(self, event):
        self._control.shutdown()

    ## actions ##

    def set_profile(self, name):
        self._control.shutdown()

        ctl = control.get_control(self._config, name)
        self.setup_control(ctl)

    def stop(self):
        self._control.stop()

    def restart(self):
        self._control.restart()

    def clear_output(self):
        print('clear')

    ## commands ##

    def evaluate(self, source):
        try:
            self._control.evaluate(source)
        except Exception as e:
            log.debug('totally normal evaluate error: %s', e)
            self.status_disconnected.emit(str(e))
        else:
            self.output_edit.append_source(source)
            self.source_edit.clear()

    def complete(self, context):
        try:
            self._control.complete(context)
        except Exception as e:
            log.debug('totally normal complete error: %s', e)
            self.status_disconnected.emit(str(e))

   ## status ##

    def _set_connected(self, address):
        if self._connected:
            return
        self._connected = True

        msg = 'connected: {}:{}'.format(*address)
        self.status_label.setText(msg)
        self.status_icon.setPixmap(self._status_pixmap_connected)

    def _set_disconnected(self, error=None, force=False):
        if not self._connected and not force:
            return
        self._connected = False

        e = error and ': {}'.format(error) or ''
        msg = 'not connected{}'.format(e)
        self.status_label.setText(msg)
        self.status_icon.setPixmap(self._status_pixmap_disconnected)
