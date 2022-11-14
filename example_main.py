import sys

from PyQt6.QtWidgets import QApplication
from reloader import ReloadWindow
import example_window

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ReloadWindow(example_window, app)
    window.show()
    sys.exit(app.exec())
