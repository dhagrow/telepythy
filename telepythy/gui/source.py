import re
import contextlib

from qtpy.QtCore import Qt
from qtpy import QtCore, QtGui, QtWidgets

from . import textedit
from .history import History

COMPLETER_KEYS = frozenset([
    Qt.Key_Return, Qt.Key_Enter, Qt.Key_Escape, Qt.Key_Tab, Qt.Key_Backtab])

_rx_context = re.compile(r'[_A-Za-z0-9.()"\'\[\]]+$')
def get_completion_context(line):
    match = _rx_context.search(line)
    return (match and match.group()) or ''

# required to let ctrl+c through (when no text is selected)
class EventFilter(QtCore.QObject):
    def eventFilter(self, obj, event):
        if isinstance(event, QtGui.QKeyEvent):
            key = event.key()
            mod = event.modifiers()
            ctrl = mod & Qt.ControlModifier

            if ctrl and key == Qt.Key_C:
                if not obj.textCursor().hasSelection():
                    return True

        return super().eventFilter(obj, event)

class SourceEdit(textedit.TextEdit):
    evaluation_requested = QtCore.Signal(str)
    completion_requested = QtCore.Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._history = History()
        self._current = None

        self.installEventFilter(EventFilter(self))

        self.setLineWrapMode(self.NoWrap)

        self.completer_model = QtGui.QStandardItemModel()
        self.completer = QtWidgets.QCompleter(self.completer_model, self)
        self.completer.setWidget(self)
        self.completer.setCompletionMode(self.completer.PopupCompletion)
        self.completer.activated[str].connect(self.complete)

        self.textChanged.connect(self.refresh_completer)

    def show_completer(self, matches):
        if not matches:
            return

        completer = self.completer
        completer.setCompletionPrefix('')

        model = self.completer_model
        model.clear()

        for match in matches:
            item = QtGui.QStandardItem(match)
            model.appendRow(item)

        # refresh first to ensure correct completion count
        self.refresh_completer(force=True)

        if completer.completionCount() == 1:
            self.complete(completer.currentCompletion())
            return

        # popup size
        popup = completer.popup()
        rect = self.cursorRect()
        scrollbar = popup.verticalScrollBar()
        rect.setWidth(popup.sizeHintForColumn(0) + scrollbar.sizeHint().width())

        completer.complete(rect)

    def refresh_completer(self, force=False):
        if not (force or self.completer.popup().isVisible()):
            return

        completer = self.completer
        popup = completer.popup()

        ident = self.completion_context().split('.')[-1]
        if not ident.strip():
            popup.hide()

        self.completer.setCompletionPrefix(ident)
        if completer.completionCount() == 0:
            popup.hide()

        item = self.completer_model.item(0)
        if item:
            popup.setCurrentIndex(item.index())

    def complete(self, match):
        ident = self.completion_context().split('.')[-1]
        text = match[len(ident):]

        self.insertPlainText(text)
        self.completer_model.clear()

    def completion_context(self):
        cur = self.textCursor()
        cur.movePosition(cur.StartOfLine, cur.KeepAnchor)
        sel = cur.selectedText()

        return get_completion_context(sel)

    def previous(self):
        if not self._history:
            return

        match = self.toPlainText()
        if self._current is None:
            self._current = match

        source = self._history.previous(match)
        if source:
            self.setPlainText(source)
            self.move_cursor_position(QtGui.QTextCursor.End)

    def next(self):
        if not self._history:
            return

        match = self.toPlainText()
        source = self._history.next(match)
        if source:
            self.setPlainText(source)
        else:
            self.setPlainText(self._current)
        self.move_cursor_position(QtGui.QTextCursor.End)

    def reset(self):
        # clear history browsing state
        self._history.reset()
        self._current = None

    def setPlainText(self, text):
        """Overridden to prevent clearing undo history."""
        self.clear()
        self.insertPlainText(text)

    def clear(self):
        cur = self.textCursor()
        cur.movePosition(cur.Start)
        cur.movePosition(cur.End, cur.KeepAnchor)
        cur.deleteChar()

    def next_cell(self):
        self.reset()

        source = self.toPlainText()
        self._history.append(source)

        self.clear()

    ## events ##

    def keyPressEvent(self, event):
        doc = self.document()
        key = event.key()
        mod = event.modifiers()
        ctrl = mod & Qt.ControlModifier

        if self.completer.popup().isVisible():
            if key in COMPLETER_KEYS:
                event.ignore()
                return

        self.ensureCursorVisible()

        if key == Qt.Key_Enter:
            # Enter (keypad) will always evaluate
            source = self.toPlainText()
            if source:
                self.evaluation_requested.emit(source)
                return

        elif key == Qt.Key_Return:
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
                spaces = doc.block_indentation(block)
                # spaces = self.block_indent(block)
                if new_scope:
                    spaces += 4
                self.insertPlainText('\n' + (' ' * spaces))
                return

        elif key == Qt.Key_Tab:
            cursor = self.textCursor()
            if not cursor.hasSelection():
                ctx = self.completion_context()
                if ctx:
                    self.completion_requested.emit(ctx)
                    return

            self.indent()
            return

        elif key == Qt.Key_Backtab:
            self.dedent()
            return

        elif ctrl and key == Qt.Key_Up:
            self.previous()
            return

        elif ctrl and key == Qt.Key_Down:
            self.next()
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

    def indent(self):
        doc = self.document()
        cursor = self.textCursor()
        block = cursor.block()
        indent = 4
        with cursor_edit(cursor):
            if cursor.hasSelection():
                start = cursor.selectionStart()
                end = cursor.selectionEnd()
                for block in reversed(doc.blocks(doc.findBlock(end))):
                    blockEnd = block.position() + block.length() - 1
                    if blockEnd < start:
                        break
                    offset = doc.block_indentation(block) % indent
                    cursor.setPosition(block.position())
                    cursor.insertText(' ' * (indent - offset))
            else:
                offset = doc.block_indentation(block) % indent
                cursor.setPosition(block.position())
                cursor.insertText(' ' * (indent - offset))

    def dedent(self):
        doc = self.document()
        indent = 4
        cursor = self.textCursor()
        with cursor_edit(cursor):
            if cursor.hasSelection():
                start = cursor.selectionStart()
                end = cursor.selectionEnd()
                blocks = reversed(doc.blocks(doc.findBlock(end)))
            else:
                start = 0
                blocks = [cursor.block()]

            for block in blocks:
                blockEnd = block.position() + block.length() - 1
                if blockEnd < start:
                    break

                blockIndent = doc.block_indentation(block)
                offset = blockIndent % indent

                cursor.setPosition(block.position() + blockIndent)
                n = min(cursor.columnNumber(), indent - offset)
                cursor.movePosition(cursor.PreviousCharacter, cursor.KeepAnchor, n)
                cursor.removeSelectedText()

    def move_cursor_position(self, position):
        cursor = self.textCursor()
        cursor.movePosition(position)
        self.setTextCursor(cursor)

@contextlib.contextmanager
def cursor_edit(cursor):
    cursor.beginEditBlock()
    try:
        yield cursor
    finally:
        cursor.endEditBlock()
