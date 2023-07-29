import collections

from qtpy.QtCore import Qt
from qtpy import QtCore, QtGui, QtWidgets

from ..lib import logs
from ..lib import start_server

from .about import AboutDialog
from .source import SourceEdit
from .output import OutputEdit
from .settings import SettingsWidget
from . import tips

# required to make resources available
from . import resources_rc

log = logs.get(__name__)

class Window(QtWidgets.QMainWindow):
    output_started = QtCore.Signal(str)
    output_stopped = QtCore.Signal()
    error_received = QtCore.Signal(str)
    stdout_received = QtCore.Signal(str)
    stderr_received = QtCore.Signal(str)
    completion_received = QtCore.Signal(list)
    status_connected = QtCore.Signal(tuple)
    status_disconnected = QtCore.Signal(str)

    def __init__(self, config, profile, profiles, debug=False):
        super().__init__()

        self._config = config

        # XXX: something to experiment with sometime
        # self.setStyleSheet("background:88ffffff;");
        # self.setAttribute(Qt.WA_TranslucentBackground);
        # self.setWindowFlags(Qt.FramelessWindowHint);

        self._control = None
        self._profile = None
        self._profiles = profiles

        self._connected = None
        self._history_result = collections.OrderedDict()

        self._debug = debug
        self._debug_server = None

        self.setup()
        self.set_profile(profile)

    ## setup ##

    def setup(self):
        self.setup_palette()
        self.setup_actions()
        self.setup_about_dialog()
        self.setup_output_edit()
        self.setup_source_edit()
        self.setup_settings_widget()
        self.setup_menus()
        self.setup_statusbar()
        self.setup_signals()

        self.settings.read_config()

        self.source_edit.setFocus()

    def setup_palette(self):
        # set default link color to something a little more light/dark friendly
        app = QtWidgets.QApplication.instance()
        pal = app.palette()
        pal.setColor(pal.ColorRole.Link, 'cadetblue')
        app.setPalette(pal)

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

    def setup_settings_widget(self):
        self.settings = SettingsWidget(self._config, self)

        self.settings_dock = QtWidgets.QDockWidget('Settings')
        self.settings_dock.setWidget(self.settings)
        self.settings_dock.setVisible(False)

        self.addDockWidget(Qt.RightDockWidgetArea, self.settings_dock)

    def setup_menus(self):
        self.main_menu = menu = QtWidgets.QMenu('File', self)
        menu.addAction(self.action_about)
        menu.addSeparator()
        menu.addAction(self.action_interrupt)
        menu.addAction(self.action_restart)
        menu.addSeparator()
        menu.addAction(self.action_quit)

        self.output_menu = menu = QtWidgets.QMenu('Output', self)
        menu.addAction(self.output_edit.action_fold_last_block)
        menu.addAction(self.output_edit.action_unfold_last_block)

        self.view_menu = menu = QtWidgets.QMenu('View', self)
        menu.addAction(self.action_toggle_menu)
        action = self.settings_dock.toggleViewAction()
        action.setShortcut('F12')
        menu.addAction(action)
        menu.addAction(self.source_dock.toggleViewAction())
        menu.addAction(self.action_toggle_source_title)

        self.profile_menu = menu = QtWidgets.QMenu('Profiles', self)
        menu.aboutToShow.connect(self.setup_profiles)
        self._profile_actions = {}

        if self._debug:
            self.debug_menu = menu = QtWidgets.QMenu('Debug', self)
            menu.addAction(self.action_debug_start)
            menu.addAction(self.action_debug_stop)

        bar = self.menuBar()
        bar.addMenu(self.main_menu)
        bar.addMenu(self.output_menu)
        bar.addMenu(self.view_menu)
        bar.addMenu(self.profile_menu)
        if self._debug:
            bar.addMenu(self.debug_menu)

        self.status_menu = menu = QtWidgets.QMenu()
        menu.addMenu(self.main_menu)
        menu.addMenu(self.output_menu)
        menu.addMenu(self.view_menu)
        menu.addMenu(self.profile_menu)
        if self._debug:
            menu.addMenu(self.debug_menu)

    def setup_profiles(self):
        menu = self.profile_menu
        group = QtWidgets.QActionGroup(menu)

        checked = False # used to prioritize config profiles
        current = self._profile
        menu.clear()

        for name in sorted(self._profiles.get_config_profiles()):
            act = QtWidgets.QAction(name, self)
            act.setCheckable(True)
            act.setActionGroup(group)

            if name == current:
                act.setChecked(True)
                checked = True

            menu.addAction(act)

        menu.addSection('virtualenvs')
        for name in sorted(self._profiles.get_virtualenv_profiles()):
            act = QtWidgets.QAction(name, self)
            act.setCheckable(True)
            act.setActionGroup(group)

            if name == current and not checked:
                act.setChecked(True)

            menu.addAction(act)

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
        self.action_interrupt.triggered.connect(self.check_interrupt)
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
        self.error_received.connect(self.output_edit.append_error)
        self.stdout_received.connect(self.output_edit.append)
        self.stderr_received.connect(self.output_edit.append)

        self.completion_received.connect(self.source_edit.show_completer)

        self.status_connected.connect(self._set_connected)
        self.status_disconnected.connect(self._set_disconnected)

    ## events ##

    def showEvent(self, event):
        if self._config['startup.show_tips']:
            # slight delay allows main window to pop up
            QtCore.QTimer.singleShot(1, self.show_tips)

    def contextMenuEvent(self, event):
        self.view_menu.exec_(event.globalPos())

    def closeEvent(self, event):
        self._control.stop()

    ## actions ##

    def show_tips(self):
        def next_tip():
            edit.clear()
            edit.appendHtml(tips.get())

        box = QtWidgets.QDialog(self)
        box.setWindowTitle('Tips')

        layout = QtWidgets.QVBoxLayout()
        box.setLayout(layout)

        edit = QtWidgets.QPlainTextEdit()
        edit.setReadOnly(True)
        layout.addWidget(edit)

        button_layout = QtWidgets.QHBoxLayout()
        layout.addLayout(button_layout)

        checkbox = QtWidgets.QCheckBox()
        checkbox.setText('Do not show again')
        def toggle_tips(state):
            self._config['startup.show_tips'] = state == Qt.Unchecked.value
            self._config.write()
        checkbox.stateChanged.connect(toggle_tips)
        button_layout.addWidget(checkbox)

        buttons = QtWidgets.QDialogButtonBox()

        buttons.addButton(buttons.StandardButton.Ok)
        buttons.accepted.connect(box.accept)

        next_button = buttons.addButton('Next', buttons.ButtonRole.ActionRole)
        next_button.clicked.connect(next_tip)

        button_layout.addWidget(buttons)

        next_tip()
        box.show()

    def set_profile(self, name):
        if self._control:
            self._control.stop()
            self._control = None
        self._set_disconnected(force=True)

        self._control = ctl = self._profiles.get_control(name)

        ctl.register(None, lambda address: self.status_connected.emit(address))
        def start(event):
            version = event['data']['version']
            self.output_started.emit(version)
        ctl.register('start', start)
        ctl.register('done', lambda _: self.output_stopped.emit())

        def error(event):
            text = event['data']['text']
            self.error_received.emit(text)
        ctl.register('error', error)

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

        def exception(err):
            log.debug('totally normal events error: %s', err)
            self.status_disconnected.emit(err)
        ctl.register('exception', exception)

        ctl.start()

        self.profile_button.setText(name)

        self._profile = name

    def restart(self):
        self._control.restart()
        self._set_disconnected(force=True)

    def check_interrupt(self):
        try:
            self.focusWidget().handle_ctrl_c()
        except AttributeError:
            self.interrupt()

    ## commands ##

    def start_session(self, version):
        self.output_edit.append_session(version)

        path = self._config['startup.source_path']
        try:
            with open(path) as f:
                source = f.read()
        except FileNotFoundError:
            log.debug('startup file not found: %s', path)
        except OSError as e:
            log.error('failed to read startup file: %s', e)
        else:
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
