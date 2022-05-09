from qtpy.QtCore import Qt
from qtpy import QtCore, QtGui

from pygments.lexers import PythonConsoleLexer

from . import textedit

PS1 = '>>> '
PS2 = '... '

class OutputEdit(textedit.TextEdit):
    def __init__(self, parent=None):
        super().__init__(PythonConsoleLexer(), parent)

        self.setReadOnly(True)
        self.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)

    ## copy ##

    def copy(self):
        clip = QtGui.QGuiApplication.clipboard()
        text = self.textCursor().selectedText()
        lines = []
        for line in text.splitlines():
            if line.startswith((PS1, PS2)):
                line = line[4:]
            lines.append(line)
        clip.setText('\n'.join(lines))

    def contextMenuEvent(self, event):
        # make sure copy menu action calls self.copy()
        menu = self.createStandardContextMenu()
        act = menu.actions()[0]
        act.triggered.disconnect()
        act.triggered.connect(self.copy)
        menu.exec_(event.globalPos())

    ## append ##

    @QtCore.Slot(str)
    def append(self, text):
        cur = self.textCursor()
        cur.movePosition(cur.End)
        cur.insertText(text)
        self.scroll_to_bottom()

    def append_session(self, version):
        cur = self.textCursor()
        cur.movePosition(cur.End)
        if self.blockCount() > 1:
            cur.insertText('\n')
        tpl = '<div style="background: {};">{}</p><p></p>'
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

    def extract_source(self):
        def collect():
            text = self.toPlainText()
            for line in text.splitlines():
                if line.startswith(PS1):
                    yield line[len(PS1):]
                elif line.startswith(PS2):
                    yield line[len(PS2):]
        return '\n'.join(collect())

    ## folding ##

    def show_block(self, block):
        block.setVisible(True)
        self.viewport().update()

    def hide_block(self, block):
        block.setVisible(False)
        self.viewport().update()
