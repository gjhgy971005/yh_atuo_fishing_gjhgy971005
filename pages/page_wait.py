from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt


class WaitingPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        label = QLabel("后续拓展保留页")
        label.setStyleSheet("font-size:20px;color:white;")
        layout.addWidget(label)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)