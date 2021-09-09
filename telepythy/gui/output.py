from qtpy import QtCore, QtGui, QtWidgets

from pygments.lexers import PythonConsoleLexer

from .highlighter import PygmentsHighlighter

PS1 = '>>> '
PS2 = '... '

class OutputEdit(QtWidgets.QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.highlighter = PygmentsHighlighter(
            self.document(), PythonConsoleLexer())

        self.setReadOnly(True)
        self.setWordWrapMode(QtGui.QTextOption.WrapAnywhere)

    def set_style(self, style):
        self.highlighter.set_style(style)
        self.set_palette()

    def set_palette(self):
        highlight = self.highlighter
        palette = self.palette()
        palette.setColor(QtGui.QPalette.Base, highlight.background_color())
        palette.setColor(QtGui.QPalette.Text, highlight.text_color())
        self.setPalette(palette)

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

    def scroll_to_bottom(self):
        scroll = self.verticalScrollBar()
        scroll.setValue(scroll.maximum())
