import re
import itertools
import collections

from qtpy.QtCore import Qt
from qtpy import QtCore, QtGui, QtWidgets

from . import lexer
from . import textedit
from .highlighter import BlockState

PS1 = '>>> '
PS2 = '... '
BUFFER_TIMEOUT = 50 # ms
BUFFER_CHUNK_SIZE = 1000 # lines

# regex to remove prompts
rx_ps = re.compile('^({}|{})'.format(PS1, PS2))

class BlockChain:
    """This shell is powered by blockchain technology."""
    def __init__(self, chain_id, document, state, start_block):
        self._chain_id = chain_id
        self._doc = document
        self._state = state

        self._fold_block = None

        self._start_block = start_block
        self._end_block = None

    @property
    def id(self):
        return self._chain_id

    @property
    def state(self):
        return self._state

    @property
    def is_folded(self):
        return bool(self._fold_block)

    @property
    def start_block(self):
        return self._start_block

    @property
    def end_block(self):
        return self._end_block

    def add_blocks(self, start_block, end_block):
        chain_id = self.id
        visible = not self.is_folded
        for block in self._doc.blocks(start_block, end_block):
            block.setUserState(chain_id)
            block.setVisible(visible)
        self._end_block = end_block

        fold_block = self._fold_block
        if fold_block:
            cur = QtGui.QTextCursor(fold_block)
            cur.movePosition(cur.NextCharacter)
            cur.movePosition(cur.NextWord, cur.KeepAnchor)
            cur.removeSelectedText()
            cur.insertText(f'{self.count() - 2} ')

    def count(self):
        return (self._end_block.blockNumber() -
            self._start_block.blockNumber() + 1)

    def blocks(self):
        yield from self._doc.blocks(self._start_block, self._end_block)

    def fold(self):
        if self.is_folded or self.count() < 3:
            return

        blocks = self.blocks()
        first_block = next(blocks) # skip first line
        for block in blocks:
            block.setVisible(False)

        # add a fold info block
        cur = QtGui.QTextCursor(first_block)
        cur.movePosition(cur.EndOfBlock)
        cur.insertBlock()
        self._fold_block = fold_block = cur.block()
        fold_block.setUserState(self.id)

        # set state context for the highlighter
        with self._doc.using_context(state=BlockState.fold):
            tpl = '[{} more lines. Double-click to unfold]'
            cur.insertText(tpl.format(self.count() - 2))

    def unfold(self):
        if not self.is_folded:
            return

        # remove the fold info block
        cur = QtGui.QTextCursor(self._fold_block)
        cur.select(cur.BlockUnderCursor)
        cur.removeSelectedText()

        for block in self.blocks():
            block.setVisible(True)

        self._fold_block = None

class OutputEdit(textedit.TextEdit):
    def __init__(self, parent=None):
        super().__init__(lexer.ConsoleLexer(), parent)

        self._buffer = []
        # timer used to flush the buffer at regular intervals
        # (see timerEvent)
        self.startTimer(BUFFER_TIMEOUT)

        self.setReadOnly(True)
        self.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)

        # tracks the cursor for the context menu
        self._context_cursor = None

        self._chains = collections.OrderedDict()
        self._last_state = None

        self.setup_actions()

    def setup_actions(self):
        self.action_fold_block = QtWidgets.QAction('Fold Block')
        self.action_fold_block.triggered.connect(lambda: self.fold_block())
        self.addAction(self.action_fold_block)

        self.action_unfold_block = QtWidgets.QAction('Unfold Block')
        self.action_unfold_block.triggered.connect(lambda: self.unfold_block())
        self.addAction(self.action_unfold_block)

        self.action_fold_last_block = QtWidgets.QAction('Fold Last Block')
        self.action_fold_last_block.setShortcut('Ctrl+[')
        self.action_fold_last_block.triggered.connect(lambda: self.fold_block(last=True))
        self.addAction(self.action_fold_last_block)

        self.action_unfold_last_block = QtWidgets.QAction('Unfold Last Block')
        self.action_unfold_last_block.setShortcut('Ctrl+]')
        self.action_unfold_last_block.triggered.connect(lambda: self.unfold_block(last=True))
        self.addAction(self.action_unfold_last_block)

        self.action_copy_source = QtWidgets.QAction('Copy Source')
        self.action_copy_source.setShortcut('Ctrl+Shift+c')
        self.action_copy_source.triggered.connect(self.copy_source)
        self.addAction(self.action_copy_source)

    ## events ##

    def timerEvent(self, event):
        self._flush_buffer()

    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()
        before = menu.actions()[-2]

        self._context_cursor = cur = self.cursorForPosition(event.pos())
        chain = self._get_chain(cur.block())
        blocks = chain.blocks()
        first_block = next(blocks)

        # is there any source at all?
        if self._source_line(first_block.text()):
            menu.insertAction(before, self.action_copy_source)

        if chain.count() > 2:
            menu.insertSeparator(before)
            menu.insertAction(before, self.action_unfold_block
                if chain.is_folded else self.action_fold_block)

        menu.exec(event.globalPos())

    def mouseDoubleClickEvent(self, event):
        cur = self.cursorForPosition(event.pos())
        block = cur.block()

        if self._is_fold_block(block):
            self._context_cursor = cur
            self.unfold_block()
            return False

        return super().mouseDoubleClickEvent(event)

    ## append ##

    @QtCore.Slot(str)
    def append(self, text='\n', state=None):
        state = BlockState.output if state is None else state
        self._buffer.append((text, state))

    @QtCore.Slot(str)
    def append_error(self, text):
        self.append(text, BlockState.error)

    @QtCore.Slot()
    def append_prompt(self):
        self.highlighter.reset()
        self.append(PS1, BlockState.source)

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
        if self.blockCount() > 1:
            self.append()

        self.append(f'{version}\n', BlockState.session)
        self.append_prompt()

    def _flush_buffer(self):
        """Transfers the contents of the output buffer to the widget."""

        buf = self._buffer
        if not buf: return
        # pull a chunk to prevent long rendering delays
        buf, self._buffer = buf[:BUFFER_CHUNK_SIZE], buf[BUFFER_CHUNK_SIZE:]

        doc = self.document()
        cur = self.textCursor()
        cur.movePosition(cur.MoveOperation.End)

        is_prompt = lambda state, text: (
            state == BlockState.source and text.startswith(PS1))

        key = lambda item: item[1]
        for state, items in itertools.groupby(buf, key):
            start_block = cur.block()

            text = ''.join(item[0] for item in items)
            # set state context for the highlighter
            with doc.using_context(state=state):
                cur.insertText(text)

            # register the block chain for this insertion

            end_block = cur.block()
            if not end_block.text():
                end_block = end_block.previous()

            if state != self._last_state or is_prompt(state, text):
                # new chain
                chain = BlockChain(len(self._chains), doc, state, start_block)
                self._chains[chain.id] = chain
            else:
                # last chain
                chain = next(reversed(self._chains.values()))

            chain.add_blocks(start_block, end_block)
            self._last_state = state

        self.scroll_to_bottom()

    ## blocks ##

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

        # find source blocks
        # XXX: should be something more efficient here using chains
        # XXX: should only copy selected text
        text = []
        for block in doc.blocks(start_block, end_block):
            chain = self._get_chain(block)
            if chain.state == BlockState.source:
                text.append(self._source_line(block.text()))

        clip.setText('\n'.join(text))

    ## folding ##

    def fold_block(self, last=False):
        if last:
            # find last unfolded chain
            for chain in reversed(self._chains.values()):
                if not chain.is_folded and chain.count() > 2:
                    break
            else:
                return
        else:
            cur = self._get_context_cursor()
            chain = self._get_chain(cur.block())

        chain.fold()
        self.reset()

    def unfold_block(self, last=False):
        if last:
            # find last folded chain
            for chain in reversed(self._chains.values()):
                if chain.is_folded:
                    break
        else:
            cur = self._get_context_cursor()
            chain = self._get_chain(cur.block())

        chain.unfold()
        self.reset()
        self.scroll_to_block(chain.end_block)

    ## internal ##

    def reset(self):
        # solution from here:
        # https://www.qtcentre.org/threads/44803-QPlainTextEdit-inherited-invisibleQTextBlock-INVALID-vertical-scroll-bar
        self.resizeEvent(QtGui.QResizeEvent(self.size(), QtCore.QSize(0, 0)))

    def _get_context_cursor(self):
        cur = self._context_cursor
        self._context_cursor = None
        return cur or self.textCursor()

    def _get_chain(self, block):
        return self._chains[block.userState()]

    def _is_fold_block(self, block):
        chain = self._get_chain(block)
        return chain._fold_block == block

    def _source_line(self, line):
        return rx_ps.sub('', line).rstrip()
