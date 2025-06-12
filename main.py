import sys
from PyQt6.QtWidgets import QApplication
from ui.main_menu import MainMenu

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainMenu()
    window.show()
    sys.exit(app.exec())
