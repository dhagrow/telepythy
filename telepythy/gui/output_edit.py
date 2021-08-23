from qtpy import QtWidgets

PS1 = '>>> '
PS2 = '... '

class OutputEdit(QtWidgets.QPlainTextEdit):
    def append(self, text):
        self.insertPlainText(text)
        self.scroll_to_bottom()

    def append_session(self, version):
        if self.blockCount() > 1:
            self.append('\n')
        tpl = '<div style="background: #444;">{}</p><p></p>'
        self.appendHtml(tpl.format(version))
        self.append_prompt()

    def append_prompt(self, prompt=PS1):
        self.append(prompt)

    def append_source(self, source):
        if not source:
            return

        insert = self.insertPlainText
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
