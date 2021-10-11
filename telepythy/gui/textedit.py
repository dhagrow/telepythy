from qtpy import QtGui, QtWidgets

from . import document
from .highlighter import PygmentsHighlighter

class TextEdit(QtWidgets.QPlainTextEdit):
    def __init__(self, lexer=None, parent=None):
        super().__init__(parent)

        doc = document.TextDocument(self)
        self.setDocument(doc)

        self.highlighter = PygmentsHighlighter(doc, lexer)

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

    def scroll_to_bottom(self):
        scroll = self.verticalScrollBar()
        scroll.setValue(scroll.maximum())
