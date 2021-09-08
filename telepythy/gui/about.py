from qtpy.QtCore import Qt
from qtpy import QtGui, QtWidgets

from .. import __version__, __revision__

class AboutDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup()

    def setup(self):
        icon_label = QtWidgets.QLabel()
        icon_label.setAlignment(Qt.AlignCenter)
        icon = QtGui.QIcon(':icon')
        icon_label.setPixmap(icon.pixmap(32))

        title = f'Telepythy {__version__}'
        title_label = QtWidgets.QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        font = title_label.font()
        font.setPointSize(16)
        font.setWeight(font.Bold)
        title_label.setFont(font)

        subtitle = f'Revision: {__revision__}'
        subtitle_label = QtWidgets.QLabel(subtitle)
        subtitle_label.setAlignment(Qt.AlignCenter)
        font = subtitle_label.font()
        font.setPointSize(10)
        subtitle_label.setFont(font)

        button = QtWidgets.QPushButton('Close')
        button.clicked.connect(self.accept)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(button)
        button_layout.addStretch(1)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)
        layout.addLayout(button_layout)

        self.setLayout(layout)