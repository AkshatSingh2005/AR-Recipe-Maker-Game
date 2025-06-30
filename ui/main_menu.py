from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

from .nutrition_app import NutritionApp
from .recipe_scanner import RecipeScannerWindow

class MainMenu(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Healthy Cart Challenge")
        self.setFixedSize(500, 400)
        self.setStyleSheet("background-color: #111; color: white;")

        self.game_window = NutritionApp()

        self.recipe_window = RecipeScannerWindow()

        layout = QVBoxLayout()

        title = QLabel("🍎 Healthy Cart Challenge")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 26px; font-weight: bold; color: #00ffcc; margin-top: 20px;")
        layout.addWidget(title)

        banner = QLabel()
        banner.setPixmap(QPixmap("assets/game_banner.png").scaledToWidth(300))
        banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(banner)

        button_style = """
            QPushButton {
                background-color: #333;
                color: #00ffcc;
                padding: 12px;
                font-size: 16px;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #00ffcc;
                color: black;
            }
        """

        start_btn = QPushButton("▶️ Start Game")
        start_btn.setStyleSheet(button_style)
        start_btn.clicked.connect(self.show_game)
        layout.addWidget(start_btn)

        instructions_btn = QPushButton("📘 Instructions")
        instructions_btn.setStyleSheet(button_style)
        instructions_btn.clicked.connect(self.show_instructions)
        layout.addWidget(instructions_btn)

        recipe_btn = QPushButton("📋 Recipe Scanner")
        recipe_btn.setStyleSheet(button_style)
        recipe_btn.clicked.connect(self.show_recipe_scanner)
        layout.addWidget(recipe_btn)

        exit_btn = QPushButton("❌ Exit")
        exit_btn.setStyleSheet(button_style)
        exit_btn.clicked.connect(self.close)
        layout.addWidget(exit_btn)

        self.setLayout(layout)

    def show_game(self):
        self.hide()
        self.game_window.show()

    def show_instructions(self):
        QMessageBox.information(
            self,
            "Instructions",
            "1. Point the camera at a product with a QR or barcode.\n"
            "2. See health analysis and ingredients.\n"
            "3. Add products to cart.\n"
            "4. Complete nutrition challenges!\n\n🥦 Stay healthy and win big!"
        )
    def show_recipe_scanner(self):
        self.recipe_window.show()
        self.hide() 