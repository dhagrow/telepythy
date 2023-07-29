from qtpy.QtCore import Qt
from qtpy import QtGui, QtWidgets

from .. import __version__

DESCRIPTION = """\
<b>A desktop shell for Python.</b><br>
<a href="https://github.com/dhagrow/telepythy">
    https://github.com/dhagrow/telepythy
</a><br>
Copyright © Miguel Turner 2022
"""

class AboutDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        flags = Qt.WindowTitleHint | Qt.WindowSystemMenuHint
        super().__init__(parent, flags)
        self.setup()

    def setup(self):
        self.setWindowTitle('About Telepythy')

        icon_label = QtWidgets.QLabel()
        icon_label.setAlignment(Qt.AlignCenter)
        icon = QtGui.QIcon(':icon')
        icon_label.setPixmap(icon.pixmap(48))

        title_label = QtWidgets.QLabel('Telepythy')
        title_label.setAlignment(Qt.AlignCenter)
        font = title_label.font()
        font.setPointSize(16)
        font.setWeight(font.Weight.Bold)
        title_label.setFont(font)

        version_label = QtWidgets.QLabel(f'Version {__version__}')

        title_layout = QtWidgets.QGridLayout()
        title_layout.addWidget(icon_label, 0, 0, 2, 1)
        title_layout.addWidget(title_label, 0, 1, 1, 1)
        title_layout.addWidget(version_label, 1, 1, 1, 1)
        title_layout.setColumnStretch(2, 2)

        frame = QtWidgets.QFrame()
        frame.setFrameShape(frame.Shape.StyledPanel)
        frame.setFrameShadow(frame.Shadow.Raised)
        frame.setLayout(title_layout)

        desc_label = QtWidgets.QLabel(DESCRIPTION)
        desc_label.setOpenExternalLinks(True)

        buttons = QtWidgets.QDialogButtonBox()
        buttons.setStandardButtons(buttons.StandardButton.Close)
        buttons.rejected.connect(self.accept)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(frame)
        layout.addWidget(desc_label)
        layout.addWidget(buttons)

        self.setLayout(layout)
