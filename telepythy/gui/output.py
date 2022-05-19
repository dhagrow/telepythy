import re
import enum
import itertools

from qtpy.QtCore import Qt
from qtpy import QtCore, QtWidgets

from pygments.lexers import PythonConsoleLexer

from . import textedit

PS1 = '>>> '
PS2 = '... '
BUFFER_TIMEOUT = 50 # ms

class BlockState(enum.IntEnum):
    source = 0
    output = 1
    session = 2

class OutputEdit(textedit.TextEdit):
    def __init__(self, parent=None):
        super().__init__(PythonConsoleLexer(), parent)

        self._buffer = []
        self.startTimer(BUFFER_TIMEOUT)

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

        menu.exec(event.globalPos())

    ## append ##

    @QtCore.Slot(str)
    def append(self, text, state=None):
        state = BlockState.output if state is None else state
        self._buffer.append((text, state))

    def _flush_buffer(self):
        buf = self._buffer
        self._buffer = []

        if not buf:
            return

        cur = self.textCursor()
        doc = self.document()

        key = lambda item: item[1]
        for state, items in itertools.groupby(buf, key):
            text = ''.join(item[0] for item in items)

            cur.movePosition(cur.End)
            start_block = cur.block()

            if state is BlockState.session:
                cur.insertHtml(text)
            else:
                cur.insertText(text)

            end_block = cur.block()

            # set state for all appended blocks
            for block in doc.blocks(start_block, end_block):
                block.setUserState(state)

        self.scroll_to_bottom()

    @QtCore.Slot()
    def append_prompt(self, prompt=PS1):
        self.append(prompt, BlockState.source)

    def append_source(self, source):
        source = source.strip()
        if not source:
            return

        lines = source.splitlines()
        text = [lines[0], '\n']
        for line in lines[1:]:
            text.extend([PS2, line, '\n'])

        self.append(''.join(text), BlockState.source)

    def append_session(self, version):
        text = []
        if self.blockCount() > 1:
            text.append('\n')

        # TODO: take style into account
        tpl = '<div style="background: {};">{}</p>'
        text.append(tpl.format('#49A0AE', version))
        text.append('<p style="background: #00000000;"></p>')

        self.append(''.join(text), BlockState.session)
        self.append_prompt()

    ## source ##

    def copy_source(self):
        clip = QtWidgets.QApplication.clipboard()

        doc = self.document()
        cur = self.textCursor()
        start = cur.selectionStart()
        end = cur.selectionEnd()

        # find selected blocks
        cur.movePosition(cur.Start)
        cur.movePosition(cur.Right, cur.MoveAnchor, start)
        start_block = cur.block()
        cur.movePosition(cur.Right, cur.KeepAnchor, end - cur.position())
        end_block = cur.block()

        # regex to remove prompts
        rx_ps = re.compile('^({}|{})'.format(PS1, PS2))

        # find source blocks
        text = []
        for block in doc.blocks(start_block, end_block):
            if block.userState() == BlockState.source:
                line = rx_ps.sub('', block.text())
                text.append(line)

        clip.setText('\n'.join(text))
