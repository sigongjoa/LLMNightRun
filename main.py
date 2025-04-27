
import sys
import os
from PyQt6.QtWidgets import QApplication
from frontend.views.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("LLM Forge")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
    