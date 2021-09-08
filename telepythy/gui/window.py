import collections

from qtpy.QtCore import Qt
from qtpy import QtCore, QtGui, QtWidgets

from ..lib import logs

from .about import AboutDialog
from .source import SourceEdit
from .output import OutputEdit
from .style import StyleWidget

log = logs.get(__name__)

class Window(QtWidgets.QMainWindow):
    output_started = QtCore.Signal(str)
    output_stopped = QtCore.Signal()
    stdout_received = QtCore.Signal(str)
    stderr_received = QtCore.Signal(str)
    completion_received = QtCore.Signal(list)
    status_connected = QtCore.Signal(tuple)
    status_disconnected = QtCore.Signal(str)

    def __init__(self, config, manager, profile):
        super().__init__()

        self._manager = manager
        self._control = None
        self._profiles = {}

        self._connected = None
        self._history_result = collections.OrderedDict()

        self.setup()
        self.config(config, profile)
        self.set_profile(profile)

    ## config ##

    def config(self, config, profile):
        self._config = config

        # font
        family = config.style.font_family
        size = config.style.font_size
        self.output_edit.setFont(QtGui.QFont(family, size))
        self.source_edit.setFont(QtGui.QFont(family, size))

        # style
        sec = config.style
        self.style_chooser.set_app_style(sec.app)
        self.style_chooser.set_highlight_style(sec.highlight)

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
            action.setChecked(name == profile)
            menu.addAction(action)
            self._profiles[name] = action

        self.resize(*config.window.size)

    ## setup ##

    def setup(self):
        self.setup_actions()
        self.setup_about_dialog()
        self.setup_output_edit()
        self.setup_source_edit()
        self.setup_style_widget()
        self.setup_menus()
        self.setup_menubar()
        self.setup_statusbar()
        self.setup_signals()

        self.source_edit.setFocus()

    def setup_actions(self):
        self.action_about = QtWidgets.QAction('About')
        self.addAction(self.action_about)

        self.action_quit = QtWidgets.QAction('Quit')
        self.action_quit.setShortcut('Ctrl+q')
        self.addAction(self.action_quit)

        self.action_interrupt = QtWidgets.QAction('Interrupt')
        self.action_interrupt.setShortcut('Ctrl+c')
        self.addAction(self.action_interrupt)

        self.action_restart = QtWidgets.QAction('Restart')
        self.action_restart.setShortcut('Ctrl+F6')
        self.addAction(self.action_restart)

        self.action_toggle_menu = QtWidgets.QAction('Menu')
        self.action_toggle_menu.setCheckable(True)
        self.action_toggle_menu.setChecked(True)

        self.action_toggle_source_title = QtWidgets.QAction('Source Titlebar')
        self.action_toggle_source_title.setCheckable(True)
        self.action_toggle_source_title.setChecked(True)

    def setup_about_dialog(self):
        self.about_dialog = AboutDialog(self)

    def setup_output_edit(self):
        self.output_edit = OutputEdit()
        self.output_edit.setReadOnly(True)
        self.output_edit.setWordWrapMode(QtGui.QTextOption.WrapAnywhere)

        self.setCentralWidget(self.output_edit)

    def setup_source_edit(self):
        self.source_edit = SourceEdit()

        self.source_dock = QtWidgets.QDockWidget('Source')
        self.source_dock.setWidget(self.source_edit)

        self.addDockWidget(Qt.BottomDockWidgetArea, self.source_dock)

    def setup_style_widget(self):
        self.style_chooser = StyleWidget()

        self.style_dock = QtWidgets.QDockWidget('Styles')
        self.style_dock.setWidget(self.style_chooser)
        self.style_dock.setVisible(False)

        self.addDockWidget(Qt.RightDockWidgetArea, self.style_dock)

    def setup_menus(self):
        self.main_menu = QtWidgets.QMenu('Main', self)
        self.main_menu.addAction(self.action_about)
        self.main_menu.addAction(self.action_restart)
        self.main_menu.addAction(self.action_quit)

        self.view_menu = QtWidgets.QMenu('View', self)
        self.view_menu.addAction(self.action_toggle_menu)
        self.view_menu.addAction(self.style_dock.toggleViewAction())
        self.view_menu.addAction(self.source_dock.toggleViewAction())
        self.view_menu.addAction(self.action_toggle_source_title)

        self.profile_menu = QtWidgets.QMenu('Profile', self)

        self.status_menu = QtWidgets.QMenu()
        self.status_menu.addMenu(self.main_menu)
        self.status_menu.addMenu(self.view_menu)
        self.status_menu.addMenu(self.profile_menu)

    def setup_menubar(self):
        bar = self.menuBar()
        bar.addMenu(self.main_menu)
        bar.addMenu(self.view_menu)
        bar.addMenu(self.profile_menu)

    def setup_statusbar(self):
        bar = self.statusBar()

        icon = QtGui.QIcon(':connected')
        self._status_pixmap_connected = icon.pixmap(16)
        icon = QtGui.QIcon(':disconnected')
        self._status_pixmap_disconnected = icon.pixmap(16)

        self.menu_button = QtWidgets.QPushButton()
        self.menu_button.setIcon(QtGui.QIcon(':menu'))
        self.menu_button.setMenu(self.status_menu)
        self.menu_button.setStyleSheet('::menu-indicator{ image: none; }')
        self.menu_button.setFlat(True)
        bar.addWidget(self.menu_button)

        self.status_label = QtWidgets.QLabel()
        bar.addPermanentWidget(self.status_label)

        self.status_icon = QtWidgets.QLabel()
        bar.addPermanentWidget(self.status_icon)

        self.profile_button = QtWidgets.QPushButton('default')
        self.profile_button.setMenu(self.profile_menu)
        self.profile_button.setStyleSheet('::menu-indicator{ image: none; }')
        self.profile_button.setFlat(True)
        bar.addPermanentWidget(self.profile_button)

    def setup_signals(self):
        self.action_about.triggered.connect(self.about_dialog.exec)
        self.action_quit.triggered.connect(self.close)
        self.action_interrupt.triggered.connect(self.interrupt)
        self.action_restart.triggered.connect(self.restart)
        self.action_toggle_menu.toggled.connect(self.menuBar().setVisible)

        def source_toggle(checked):
            w = None if checked else QtWidgets.QWidget(self.source_dock)
            self.source_dock.setTitleBarWidget(w)
        self.action_toggle_source_title.toggled.connect(source_toggle)

        self.profile_menu.triggered.connect(
            lambda action: self.set_profile(action.text()))

        self.source_edit.evaluation_requested.connect(self.evaluate)
        self.source_edit.completion_requested.connect(self.complete)

        self.output_started.connect(self.start_session)
        self.output_stopped.connect(self.output_edit.append_prompt)
        self.stdout_received.connect(self.output_edit.append)
        self.stderr_received.connect(self.output_edit.append)

        self.completion_received.connect(self.source_edit.show_completer)

        self.status_connected.connect(self._set_connected)
        self.status_disconnected.connect(self._set_disconnected)

        self.style_chooser.highlight_style_changed.connect(
            self.output_edit.set_style)
        self.style_chooser.highlight_style_changed.connect(
            self.source_edit.set_style)

    ## events ##

    def contextMenuEvent(self, event):
        self.view_menu.exec_(event.globalPos())

    def closeEvent(self, event):
        self._control.shutdown()

    ## actions ##

    def set_profile(self, name):
        action = self._profiles[name]

        if self._control:
            self._control.shutdown()
        self._set_disconnected(force=True)

        self._control = ctl = self._manager.get_control(name)

        ctl.register(None, lambda address: self.status_connected.emit(address))
        def start(event):
            version = event['data']['version']
            self.output_started.emit(version)
        ctl.register('start', start)
        ctl.register('done', lambda _: self.output_stopped.emit())

        def stdout(event):
            text = event['data']['text']
            self.stdout_received.emit(text)
        ctl.register('stdout', stdout)

        def stderr(event):
            text = event['data']['text']
            self.stderr_received.emit(text)
        ctl.register('stderr', stderr)

        def completion(event):
            matches = event['data']['matches']
            self.completion_received.emit(matches)
        ctl.register('completion', completion)

        def error(err):
            log.debug('totally normal events error: %s', err)
            self.status_disconnected.emit(err)
        ctl.register('error', error)

        ctl.init()

        self.profile_menu.setActiveAction(action)
        self.profile_button.setText(name)

    def stop(self):
        self._control.stop()

    def restart(self):
        self._control.restart()

    ## commands ##

    def start_session(self, version):
        self.output_edit.append_session(version)

        source = self._config.startup.source
        if source:
            self._control.evaluate(source, notify=False)

    def evaluate(self, source):
        try:
            self._control.evaluate(source)
        except Exception as e:
            log.debug('totally normal evaluate error: %s', e)
            self.status_disconnected.emit(str(e))
        else:
            self.output_edit.append_source(source)
            self.source_edit.next_cell()

    def interrupt(self):
        try:
            self._control.interrupt()
        except Exception as e:
            log.debug('totally normal interrupt error: %s', e)
            self.status_disconnected.emit(str(e))

    def complete(self, context):
        try:
            self._control.complete(context)
        except Exception as e:
            log.debug('totally normal complete error: %s', e)
            self.status_disconnected.emit(str(e))

    ## status ##

    def _set_connected(self, address):
        if self._connected == address:
            return
        self._connected = address

        msg = 'connected: {}:{}'.format(*address)
        self.status_label.setText(msg)
        self.status_icon.setPixmap(self._status_pixmap_connected)

    def _set_disconnected(self, error=None, force=False):
        if self._connected is None and not force:
            return
        self._connected = None

        e = error and ': {}'.format(error) or ''
        msg = 'not connected{}'.format(e)
        self.status_label.setText(msg)
        self.status_icon.setPixmap(self._status_pixmap_disconnected)
