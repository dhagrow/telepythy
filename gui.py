import re
import threading
import collections

from PySide2.QtCore import Qt
from PySide2 import QtCore, QtGui, QtWidgets

from client import Client

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

        self.source_edit.executed.connect(self.execute)

        self.output_received.connect(self.append)
        self.status_connected.connect(self._set_connected)
        self.status_disconnected.connect(self._set_disconnected)

        start_thread(self._output)

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

        self.source_edit = TextEdit()
        self.source_edit.setFont(QtGui.QFont('Fira Mono', 13))

        palette = self.source_edit.palette()
        palette.setColor(QtGui.QPalette.Base, '#333')
        palette.setColor(QtGui.QPalette.Text, Qt.white)
        self.source_edit.setPalette(palette)

        self.bottom_dock = QtWidgets.QDockWidget()
        self.bottom_dock.setWidget(self.source_edit)
        self.bottom_dock.setTitleBarWidget(QtWidgets.QWidget())
        self.bottom_dock.setFeatures(self.bottom_dock.DockWidgetVerticalTitleBar)

        self.addDockWidget(Qt.BottomDockWidgetArea, self.bottom_dock)

        self.addAction(self.action_quit)
        self.setCentralWidget(self.output_edit)

        self.source_edit.setFocus()
        self._set_disconnected()

    def execute(self, source):
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
        print('prompt1', cur.position())
        cur.insertText(PS1)
        self._prompt_pos = cur.position()
        print('prompt2', cur.position())

    def append_source(self, source):
        insert = self.output_edit.insertPlainText
        lines = source.splitlines()
        insert(lines[0] + '\n')
        for line in lines[1:]:
            insert(PS2)
            insert(line + '\n')
        self.append_prompt()

    def append(self, text):
        print('append0', repr(text))
        self.output_edit.insertPlainText(text)
        scroll = self.output_edit.verticalScrollBar()
        scroll.setValue(scroll.maximum())

        cur = self.output_edit.textCursor()
        print('append1', cur.position())
        cur.setPosition(self._prompt_pos)
        print('append2', cur.position())
        cur.movePosition(cur.PreviousCharacter, cur.KeepAnchor, len(PS1))
        cur.removeSelectedText()
        print('append3', cur.position())

        self.append_prompt()

    def _output(self):
        addr = self._address
        client = None

        while True:
            try:
                if client is None:
                    client = Client(addr, timeout=3)
                for line in client.output():
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

class TextEdit(QtWidgets.QPlainTextEdit):
    executed = QtCore.Signal(str)

    def __init__(self):
        super().__init__()

        self._index = 0
        self._history = []

    def clear(self):
        source = self.toPlainText()

        self._index = 0
        if source.strip():
            self._history.append(source)

        super().clear()

    def previous(self):
        if not self._history:
            return

        self._index -= 1
        try:
            source = self._history[self._index]
        except IndexError:
            self._index += 1
        else:
            self.setPlainText(source)
            self.moveCursorPosition(QtGui.QTextCursor.End)

    ## events ##

    def keyPressEvent(self, event):
        key = event.key()
        mod = event.modifiers()
        ctrl = mod & Qt.ControlModifier

        if key == Qt.Key_Return:
            # only execute when all of the following are true:
            # - there is only one line
            # - the text cursor is at the end of the text
            # - the last character is not a space
            # - the last non-space character is not a colon
            # execution can be forced by holding control
            cursor = self.textCursor()
            block = cursor.block()
            text = block.text()

            one_line = self.blockCount() == 1
            at_end = cursor.atEnd()
            no_space = text and text[-1] != ' '
            text_s = text.rstrip()
            new_scope = text_s and (text_s[-1] == ':')

            if ctrl or (one_line and at_end and no_space and not new_scope):
                self.executed.emit(self.toPlainText())
                return
            else:
                spaces = self.block_indent(block)
                self.insertPlainText('\n' + (' ' * spaces))
                return

        elif ctrl and key == Qt.Key_Up:
            self.previous()
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

    app.exec_()

if __name__ == '__main__':
    main()
