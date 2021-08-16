import threading
import collections

from PySide2.QtCore import Qt
from PySide2 import QtCore, QtGui, QtWidgets

from pygments.lexers import PythonConsoleLexer

from ..client import Client
from ..threads import start_thread

from .source_edit import SourceEdit
from .style_widget import StyleWidget
from .highlighter import PygmentsHighlighter

PS1 = '>>> '
PS2 = '... '

class Window(QtWidgets.QMainWindow):
    output_received = QtCore.Signal(str)
    status_connected = QtCore.Signal(tuple)
    status_disconnected = QtCore.Signal(str)

    def __init__(self, address):
        super().__init__()

        self._address = address
        self._client = None

        self.setup()

        self._history_result = collections.OrderedDict()
        self._prompt_pos = 0

        self.append_prompt()
        self._set_disconnected()

        self._stop_output = threading.Event()
        self._output_thread = start_thread(self._output)

    def setup(self):
        self.setup_actions()
        self.setup_output_edit()
        self.setup_source_edit()
        self.setup_style_widget()
        self.setup_signals()

        self.source_edit.setFocus()

        self.output_highlighter.set_style('gruvbox-dark')
        self.source_highlighter.set_style('gruvbox-dark')

    def setup_actions(self):
        self.action_quit = QtWidgets.QAction()
        self.action_quit.setShortcut('Ctrl+q')
        self.addAction(self.action_quit)

    def setup_style_widget(self):
        self.style_chooser = StyleWidget()

        self.right_dock = QtWidgets.QDockWidget('styles')
        self.right_dock.setWidget(self.style_chooser)
        self.right_dock.setVisible(False)

        self.addDockWidget(Qt.RightDockWidgetArea, self.right_dock)

    def setup_output_edit(self):
        self.output_edit = QtWidgets.QPlainTextEdit()
        self.output_edit.setFont(QtGui.QFont('Fira Mono', 13))
        self.output_edit.setReadOnly(True)

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

    def setup_signals(self):
        self.action_quit.triggered.connect(self.close)
        self.source_edit.evaluation_requested.connect(self.evaluate)

        self.output_received.connect(self.append)
        self.status_connected.connect(self._set_connected)
        self.status_disconnected.connect(self._set_disconnected)

        self.style_chooser.output_style_changed.connect(
            self.output_highlighter.set_style)
        self.style_chooser.source_style_changed.connect(
            self.source_highlighter.set_style)

    def evaluate(self, source):
        self.append_source(source)

        if self._client is None:
            self._client = Client(self._address)

        try:
            needs_input = self._client.evaluate(source)
        except Exception as e:
            self.status_disconnected.emit(str(e))
        else:
            if not needs_input:
                self.source_edit.clear()

    def append_prompt(self, prompt=PS1):
        cur = self.output_edit.textCursor()
        cur.insertText(prompt)
        self._prompt_pos = cur.position()

        scroll = self.output_edit.verticalScrollBar()
        scroll.setValue(scroll.maximum())

    def append_source(self, source):
        if not source:
            return

        insert = self.output_edit.insertPlainText
        lines = source.splitlines()
        insert(lines[0] + '\n')

        # XXX: remove trailing empty lines

        for line in lines[1:]:
            insert(PS2)
            insert(line + '\n')

        self.append_prompt()

    def append(self, text):
        self.output_edit.insertPlainText(text)

        cur = self.output_edit.textCursor()
        cur.setPosition(self._prompt_pos)
        cur.movePosition(cur.PreviousCharacter, cur.KeepAnchor, len(PS1))
        cur.removeSelectedText()

        self.append_prompt()

    def stop_output(self, timeout=None):
        self._stop_output.set()
        self._output_thread.join(timeout)

    def _output(self):
        addr = self._address
        client = None
        stop = self._stop_output

        while not stop.is_set():
            try:
                if client is None:
                    client = Client(addr, timeout=3)

                for line in client.output():
                    if stop.is_set():
                        break

                    self.status_connected.emit(addr)
                    if line is not None:
                        self.output_received.emit(line)

            except Exception as e:
                client = None
                self.status_disconnected.emit(str(e))

    def _set_connected(self, address):
        msg = 'connected: {}:{}'.format(*address)
        self.statusBar().showMessage(msg)

    def _set_disconnected(self, error=None):
        e = error and ': {}'.format(error) or ''
        msg = 'not connected{}'.format(e)
        self.statusBar().showMessage(msg)
