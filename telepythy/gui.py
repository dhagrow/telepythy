import re
import threading
import collections

from PySide2.QtCore import Qt
from PySide2 import QtCore, QtGui, QtWidgets

from .client import Client
from .history import History

URL = 'tcp://localhost:6336'
PS1 = '>>> '
PS2 = '... '

_rx_indent = re.compile(r'^(\s*)')

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

        # signals

        self.action_quit.triggered.connect(self.close)
        self.source_edit.evaluation_requested.connect(self.evaluate)

        self.output_received.connect(self.append)
        self.status_connected.connect(self._set_connected)
        self.status_disconnected.connect(self._set_disconnected)

        self._stop_output = threading.Event()
        self._output_thread = start_thread(self._output)

    def setup(self):
        self.action_quit = QtWidgets.QAction()
        self.action_quit.setShortcut(QtGui.QKeySequence.Quit)

        self.output_edit = QtWidgets.QPlainTextEdit()
        self.output_edit.setFont(QtGui.QFont('Fira Mono', 13))
        self.output_edit.setReadOnly(True)

        palette = self.output_edit.palette()
        palette.setColor(QtGui.QPalette.Base, '#333')
        palette.setColor(QtGui.QPalette.Text, Qt.white)
        self.output_edit.setPalette(palette)

        self.source_edit = SourceEdit()
        self.source_edit.setFont(QtGui.QFont('Fira Mono', 13))

        palette = self.source_edit.palette()
        palette.setColor(QtGui.QPalette.Base, '#333')
        palette.setColor(QtGui.QPalette.Text, Qt.white)
        self.source_edit.setPalette(palette)

        self.bottom_dock = QtWidgets.QDockWidget()
        self.bottom_dock.setWidget(self.source_edit)
        self.bottom_dock.setTitleBarWidget(QtWidgets.QWidget(self.bottom_dock))
        self.bottom_dock.setFeatures(self.bottom_dock.DockWidgetVerticalTitleBar)

        self.addDockWidget(Qt.BottomDockWidgetArea, self.bottom_dock)

        self.addAction(self.action_quit)
        self.setCentralWidget(self.output_edit)

        self.source_edit.setFocus()
        self._set_disconnected()

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
        cur.insertText(PS1)
        self._prompt_pos = cur.position()

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
        scroll = self.output_edit.verticalScrollBar()
        scroll.setValue(scroll.maximum())

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

class SourceEdit(QtWidgets.QPlainTextEdit):
    evaluation_requested = QtCore.Signal(str)

    def __init__(self):
        super().__init__()

        self._history = History()
        self._current = None

    def previous(self):
        if not self._history:
            return

        match = self.toPlainText()
        if self._current is None:
            self._current = match

        source = self._history.previous(match)
        if source:
            self.setPlainText(source)
            self.moveCursorPosition(QtGui.QTextCursor.End)

    def next(self):
        if not self._history:
            return

        match = self.toPlainText()
        source = self._history.next(match)
        if source:
            self.setPlainText(source)
        else:
            self.setPlainText(self._current)
        self.moveCursorPosition(QtGui.QTextCursor.End)

    def reset(self):
        self._history.reset()
        self._current = None

    def clear(self):
        self.reset()

        source = self.toPlainText()
        self._history.append(source)

        super().clear()

    ## events ##

    def keyPressEvent(self, event):
        key = event.key()
        mod = event.modifiers()
        ctrl = mod & Qt.ControlModifier

        if key == Qt.Key_Return:
            # only evaluate when all of the following are true:
            # - there is only one line
            # - the text cursor is at the end of the text
            # - the last character is not a space
            # - the last non-space character is not a colon
            # evaluation can be forced by holding control
            cursor = self.textCursor()
            block = cursor.block()
            text = block.text()

            one_line = self.blockCount() == 1
            at_end = cursor.atEnd()
            no_space = text and text[-1] != ' '
            text_s = text.rstrip()
            new_scope = text_s and (text_s[-1] == ':')

            if ctrl or (one_line and at_end and no_space and not new_scope):
                source = self.toPlainText()
                if source:
                    self.evaluation_requested.emit(source)
                return
            else:
                spaces = self.block_indent(block)
                if new_scope:
                    spaces += 4
                self.insertPlainText('\n' + (' ' * spaces))
                return

        elif ctrl and key == Qt.Key_Up:
            self.previous()
            return

        elif ctrl and key == Qt.Key_Down:
            self.next()
            return

        elif key == Qt.Key_Tab:
            self.insertPlainText(' ' * 4)
            return

        elif key == Qt.Key_Backspace:
            cursor = self.textCursor()
            text = cursor.block().text()[:cursor.positionInBlock()]
            if text.startswith(' ') and not text.strip(' '):
                cursor.movePosition(cursor.PreviousCharacter,
                    cursor.KeepAnchor, 4)
                cursor.deleteChar()
                return

        self.reset()

        super().keyPressEvent(event)

    ## utils ##

    def blocks(self, start=None):
        return BlockIterator(start or self.firstVisibleBlock())

    def block_indent(self, block):
        for prev in reversed(self.blocks(block)):
            spaces = _rx_indent.match(prev.text()).group(0)
            if spaces:
                return len(spaces)
        return 0

    def moveCursorPosition(self, position):
        cursor = self.textCursor()
        cursor.movePosition(position)
        self.setTextCursor(cursor)

class BlockIterator:
    def __init__(self, start):
        self._start = start

    def __iter__(self):
        block = self._start
        while block.isValid():
            yield block
            block = block.next()

    def __reversed__(self):
        block = self._start
        while block.isValid():
            yield block
            block = block.previous()

def start_thread(func, *args, **kwargs):
    t = threading.Thread(target=func, args=args, kwargs=kwargs)
    t.daemon = True
    t.start()
    return t

def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-H', '--host', default='localhost')
    parser.add_argument('-P', '--port', required=True)

    args = parser.parse_args()

    app = QtWidgets.QApplication()

    win = Window((args.host, args.port))
    win.show()

    try:
        app.exec_()
    except KeyboardInterrupt:
        pass
    finally:
        win.stop_output(timeout=1)

if __name__ == '__main__':
    main()
