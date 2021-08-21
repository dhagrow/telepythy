from PySide2 import QtWidgets

PS1 = '>>> '
PS2 = '... '

class OutputEdit(QtWidgets.QPlainTextEdit):
    def append(self, text):
        self.insertPlainText(text)
        self.scroll_to_bottom()

    def append_session(self):
        if self.blockCount() > 1:
            self.append('\n')
        self.append('[new session]\n')
        self.append_prompt()

    def append_prompt(self, prompt=PS1):
        self.append(prompt)

    def append_source(self, source):
        if not source:
            return

        insert = self.insertPlainText
        lines = source.splitlines()
        insert(lines[0] + '\n')

        # XXX: remove trailing empty lines

        for line in lines[1:]:
            insert(PS2)
            insert(line + '\n')

        self.scroll_to_bottom()

    def toSource(self):
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
