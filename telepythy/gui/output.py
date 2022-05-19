import threading

from qtpy.QtCore import Qt
from qtpy import QtCore, QtWidgets

from pygments.lexers import PythonConsoleLexer

from . import textedit

PS1 = '>>> '
PS2 = '... '

class OutputEdit(textedit.TextEdit):
    def __init__(self, parent=None):
        super().__init__(PythonConsoleLexer(), parent)

        self._buffer = []
        self._buffer_lock = threading.Lock()
        self.startTimer(50)

        self.setReadOnly(True)
        self.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)

        self.action_copy_source = QtWidgets.QAction('Copy Source')
        self.action_copy_source.setShortcut('Ctrl+Shift+c')
        self.action_copy_source.triggered.connect(self.copy_source)
        self.addAction(self.action_copy_source)

    def timerEvent(self, event):
        self._flush_buffer()

    ## menu ##

    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()
        before = menu.actions()[1]
        menu.insertAction(before, self.action_copy_source)

        menu.exec_(event.globalPos())

    ## append ##

    @QtCore.Slot(str)
    def append(self, text):
        with self._buffer_lock:
            self._buffer.append(text)

    def _flush_buffer(self):
        with self._buffer_lock:
            text = ''.join(self._buffer)
            del self._buffer[:]

        if text:
            cur = self.textCursor()
            cur.movePosition(cur.End)
            cur.insertText(text)
            self.scroll_to_bottom()

    def append_session(self, version):
        cur = self.textCursor()
        cur.movePosition(cur.End)
        if self.blockCount() > 1:
            cur.insertText('\n')
        tpl = '<div style="background: {};">{}</p><p style="background: #00000000;"></p>'
        cur.insertHtml(tpl.format('#49A0AE', version))
        # cur.insertHtml(tpl.format(self.highlighter.highlight_color(), version))
        self.append_prompt()

    @QtCore.Slot(str)
    def append_prompt(self, prompt=PS1):
        self.append(prompt)

    def append_source(self, source):
        if not source:
            return

        cur = self.textCursor()
        cur.movePosition(cur.End)
        insert = cur.insertText
        lines = source.splitlines()
        insert(lines[0] + '\n')

        # TODO: remove trailing empty lines

        for line in lines[1:]:
            insert(PS2)
            insert(line + '\n')

        self.scroll_to_bottom()

    ## source ##

    def copy_source(self):
        clip = QtWidgets.QApplication.clipboard()

        # extend selection to include full lines
        cur = self.textCursor()
        start = cur.selectionStart()
        end = cur.selectionEnd()

        cur.movePosition(cur.Start)
        cur.movePosition(cur.Right, cur.MoveAnchor, start)
        cur.movePosition(cur.StartOfLine, cur.MoveAnchor)
        cur.movePosition(cur.Right, cur.KeepAnchor, end - cur.position())
        cur.movePosition(cur.EndOfLine, cur.KeepAnchor)

        text = cur.selectedText()
        clip.setText(self.extract_source(text))

    def extract_source(self, text=None):
        def collect(text):
            for line in text.splitlines():
                if line.startswith(PS1):
                    yield line[len(PS1):]
                elif line.startswith(PS2):
                    yield line[len(PS2):]
        return '\n'.join(collect(text or self.toPlainText()))

    ## folding ##

    def show_block(self, block):
        block.setVisible(True)
        self.viewport().update()

    def hide_block(self, block):
        block.setVisible(False)
        self.viewport().update()
