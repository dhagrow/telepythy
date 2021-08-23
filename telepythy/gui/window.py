import threading
import collections

from qtpy.QtCore import Qt
from qtpy import QtCore, QtGui, QtWidgets

from pygments.lexers import PythonConsoleLexer

from .. import logs
from .. import utils

from .source_edit import SourceEdit
from .output_edit import OutputEdit
from .style_widget import StyleWidget
from .interpreter_widget import InterpreterWidget
from .highlighter import PygmentsHighlighter

log = logs.get(__name__)

class Window(QtWidgets.QMainWindow):
    output_started = QtCore.Signal()
    output_stopped = QtCore.Signal()
    output_received = QtCore.Signal(str)
    completion_received = QtCore.Signal(list)
    status_connected = QtCore.Signal(tuple)
    status_disconnected = QtCore.Signal(str)

    def __init__(self, config, manager):
        super().__init__()

        self.setup()
        self.config(config)

        self._manager = manager
        self._control = manager.get_control()
        self.setup_control()

        self._connected = False
        self._history_result = collections.OrderedDict()

        self._set_disconnected(force=True)

    ## config ##

    def config(self, config):
        self.output_highlighter.set_style('gruvbox-dark')
        self.source_highlighter.set_style('gruvbox-dark')

        self.interpreter_chooser.set_python_exec('/usr/bin/env python')

        self.resize(config['window.size'])

    ## setup ##

    def setup_control(self):
        ctl = self._control

        ctl.register(None, lambda address: self.status_connected.emit(address))
        ctl.register('start', lambda _: self.output_started.emit())
        ctl.register('done', lambda _: self.output_stopped.emit())

        def output(event):
            text = event['data']['text']
            self.output_received.emit(text)
        ctl.register('output', output)

        def completion(event):
            matches = event['data']['matches']
            self.completion_received.emit(matches)
        ctl.register('completion', completion)

        def error(exc):
            log.debug('totally normal events error: %s', exc)
            self.status_disconnected.emit(str(exc))
        ctl.register('error', error)

    def setup(self):
        self.setup_actions()
        self.setup_output_edit()
        self.setup_source_edit()
        self.setup_style_widget()
        self.setup_interpreter_widget()
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

        self.bottom_dock = QtWidgets.QDockWidget('source')
        self.bottom_dock.setWidget(self.source_edit)
        self.bottom_dock.setTitleBarWidget(QtWidgets.QWidget(self.bottom_dock))
        self.bottom_dock.setFeatures(self.bottom_dock.DockWidgetVerticalTitleBar)

        self.addDockWidget(Qt.BottomDockWidgetArea, self.bottom_dock)

    def setup_style_widget(self):
        self.style_chooser = StyleWidget()

        self.style_dock = QtWidgets.QDockWidget('styles')
        self.style_dock.setWidget(self.style_chooser)
        self.style_dock.setVisible(False)

        self.addDockWidget(Qt.RightDockWidgetArea, self.style_dock)

    def setup_interpreter_widget(self):
        self.interpreter_chooser = InterpreterWidget()

        self.interpreter_dock = QtWidgets.QDockWidget('interpreters')
        self.interpreter_dock.setWidget(self.interpreter_chooser)
        self.interpreter_dock.setVisible(False)

        self.addDockWidget(Qt.RightDockWidgetArea, self.interpreter_dock)

    def setup_menubar(self):
        bar = self.menuBar()

        menu = bar.addMenu('File')
        menu.addAction(self.action_clear)
        menu.addAction(self.action_restart)
        menu.addAction(self.action_quit)

    def setup_statusbar(self):
        bar = self.statusBar()

        style = QtWidgets.QApplication.style()
        icon = style.standardIcon(QtWidgets.QStyle.SP_DialogYesButton)
        self._status_pixmap_connected = icon.pixmap(16)
        icon = style.standardIcon(QtWidgets.QStyle.SP_DialogNoButton)
        self._status_pixmap_disconnected = icon.pixmap(16)

        self.status_label = QtWidgets.QLabel()
        bar.addPermanentWidget(self.status_label)

        self.status_icon = QtWidgets.QLabel()
        bar.addPermanentWidget(self.status_icon)

    def setup_signals(self):
        self.action_quit.triggered.connect(self.close)
        self.action_restart.triggered.connect(self.restart)
        self.action_clear.triggered.connect(self.clear_output)

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

    def closeEvent(self, event):
        self._control.shutdown()

    ## actions ##

    def stop(self):
        self._control.stop()

    def restart(self):
        self._control.restart()

    def clear_output(self):
        print('clear')

    ## commands ##

    def evaluate(self, source):
        self._control.evaluate(source)
        self.output_edit.append_source(source)
        self.source_edit.clear()

    def complete(self, context):
        self._control.complete(context)

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
