from qtpy.QtCore import Qt
from qtpy import QtCore, QtGui, QtWidgets

from . import document
from .highlighter import PygmentsHighlighter

class TextEdit(QtWidgets.QPlainTextEdit):
    interrupt_requested = QtCore.Signal()

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

    def handle_ctrl_c(self):
        if self.textCursor().hasSelection():
            self.copy()
        else:
            self.interrupt_requested.emit()

    def keyPressEvent(self, event):
        key = event.key()
        mod = event.modifiers()
        ctrl = mod & Qt.ControlModifier

        if ctrl and key == Qt.Key_C:
            self.handle_ctrl_c()
        else:
            super().keyPressEvent(event)