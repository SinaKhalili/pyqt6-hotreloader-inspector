from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QLabel,
    QMainWindow,
)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(600, 600)
        self.resize(1080, 1080)
        self.setWindowTitle("My reloading pyqt app")

        # self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)

        self.label = QLabel("Hello! yaay!")
        self.label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.label.setStyleSheet("font-size: 40px;")
        self.label.setMaximumHeight(50)

        self.setCentralWidget(self.label)