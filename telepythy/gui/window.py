import collections

from qtpy.QtCore import Qt
from qtpy import QtCore, QtGui, QtWidgets

from ..lib import logs
from ..lib import start_server

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

    def __init__(self, config, manager, profile, debug=False):
        super().__init__()

        self._manager = manager
        self._control = None

        self._connected = None
        self._history_result = collections.OrderedDict()

        self._debug = debug
        self._debug_server = None

        self.setup()
        self.config(config)
        self.set_profile(profile)

    ## config ##

    def config(self, config):
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

        self.resize(*config.window.size)

    ## setup ##

    def setup(self):
        self.setup_actions()
        self.setup_about_dialog()
        self.setup_output_edit()
        self.setup_source_edit()
        self.setup_style_widget()
        self.setup_profiles()
        self.setup_menus()
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

        if self._debug:
            self.action_debug_start = QtWidgets.QAction('Start Introspection')
            self.action_debug_stop = QtWidgets.QAction('Stop Introspection')

    def setup_about_dialog(self):
        self.about_dialog = AboutDialog(self)

    def setup_output_edit(self):
        self.output_edit = OutputEdit()
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

    def setup_profiles(self):
        self.profile_menu = menu = QtWidgets.QMenu('Profiles', self)
        self.profile_group = group = QtWidgets.QActionGroup(self.profile_menu)
        self._profile_actions = actions = {}

        for name in sorted(self._manager.get_config_profiles()):
            act = QtWidgets.QAction(name, self)
            act.setCheckable(True)
            act.setActionGroup(group)
            menu.addAction(act)
            actions[name] = act

        menu.addSection('virtualenvs')
        for name in sorted(self._manager.get_virtualenv_profiles()):
            act = QtWidgets.QAction(name, self)
            act.setCheckable(True)
            act.setActionGroup(group)
            menu.addAction(act)
            actions[name] = act

    def setup_menus(self):
        self.main_menu = QtWidgets.QMenu('File', self)
        self.main_menu.addAction(self.action_about)
        self.main_menu.addSeparator()
        self.main_menu.addAction(self.action_interrupt)
        self.main_menu.addAction(self.action_restart)
        self.main_menu.addSeparator()
        self.main_menu.addAction(self.action_quit)

        self.edit_menu = QtWidgets.QMenu('Edit', self)
        self.edit_menu.addAction(self.output_edit.action_clear)

        self.view_menu = QtWidgets.QMenu('View', self)
        self.view_menu.addAction(self.action_toggle_menu)
        self.view_menu.addAction(self.style_dock.toggleViewAction())
        self.view_menu.addAction(self.source_dock.toggleViewAction())
        self.view_menu.addAction(self.action_toggle_source_title)

        if self._debug:
            self.debug_menu = QtWidgets.QMenu('Debug', self)
            self.debug_menu.addAction(self.action_debug_start)
            self.debug_menu.addAction(self.action_debug_stop)

        bar = self.menuBar()
        bar.addMenu(self.main_menu)
        bar.addMenu(self.edit_menu)
        bar.addMenu(self.view_menu)
        bar.addMenu(self.profile_menu)
        if self._debug:
            bar.addMenu(self.debug_menu)

        self.status_menu = QtWidgets.QMenu()
        self.status_menu.addMenu(self.main_menu)
        self.status_menu.addMenu(self.edit_menu)
        self.status_menu.addMenu(self.view_menu)
        self.status_menu.addMenu(self.profile_menu)
        if self._debug:
            self.status_menu.addMenu(self.debug_menu)

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
        self.action_interrupt.triggered.connect(
            lambda: self.focusWidget().handle_ctrl_c())
        self.action_restart.triggered.connect(self.restart)

        self.action_toggle_menu.toggled.connect(self.menuBar().setVisible)

        def source_toggle(checked):
            w = None if checked else QtWidgets.QWidget(self.source_dock)
            self.source_dock.setTitleBarWidget(w)
        self.action_toggle_source_title.toggled.connect(source_toggle)

        if self._debug:
            self.action_debug_start.triggered.connect(self.start_debug_server)
            self.action_debug_stop.triggered.connect(self.stop_debug_server)

        self.profile_menu.triggered.connect(
            lambda act: self.set_profile(act.text()))

        self.source_edit.interrupt_requested.connect(self.interrupt)
        self.output_edit.interrupt_requested.connect(self.interrupt)

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
        self._control.stop()

    ## actions ##

    def set_profile(self, name):
        if self._control:
            self._control.stop()
            self._control = None
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

        ctl.start()

        self.profile_button.setText(name)
        self._profile_actions[name].setChecked(True)

    def restart(self):
        self._control.restart()
        self._set_disconnected(force=True)

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

    ## debug ##

    def start_debug_server(self):
        if not self._debug_server:
            self._debug_server = start_server({'window': self})
            log.warning('debug server started')

    def stop_debug_server(self):
        if self._debug_server:
            log.debug('debug server stopping')
            self._debug_server.stop()
            self._debug_server.join()
            self._debug_server = None
            log.warning('debug server stopped')
