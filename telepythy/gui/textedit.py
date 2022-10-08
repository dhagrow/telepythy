from qtpy.QtCore import Qt
from qtpy import QtCore, QtGui, QtWidgets

from . import document
from .highlighter import Highlighter

DEFAULT_STYLESHEET = 'QPlainTextEdit:focus { border: none; }'

class TextEdit(QtWidgets.QPlainTextEdit):
    interrupt_requested = QtCore.Signal()

    def __init__(self, lexer, parent=None):
        super().__init__(parent)

        doc = document.TextDocument(self)
        self.setDocument(doc)

        self.highlighter = Highlighter(lexer, doc)

        self.setWordWrapMode(QtGui.QTextOption.WrapAnywhere)
        self.setStyleSheet(DEFAULT_STYLESHEET)

    def set_style(self, style):
        self.highlighter.set_style(style)

        tpl = 'QPlainTextEdit { color: %s; background: %s; }' + DEFAULT_STYLESHEET
        self.setStyleSheet(tpl % (style.text_color, style.background_color))

    def scroll_to_block(self, block):
        scroll = self.verticalScrollBar()
        scroll.setValue(block.blockNumber())

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
