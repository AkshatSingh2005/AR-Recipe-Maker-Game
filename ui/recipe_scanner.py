from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from .nutrition_app import NutritionApp
from .recipe_nutrition_scanner import RecipeNutritionScanner  # Import the new widget

class RecipeScannerWindow(QWidget):
    def __init__(self, main_menu=None):
        super().__init__()
        self.setWindowTitle("📋 Recipe Scanner")
        self.setFixedSize(460, 500)
        self.setStyleSheet("background-color: #121212; color: white;")
        self.scan_window = None
        self.main_menu = main_menu

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 🔙 Back Button (top-left)
        back_btn_layout = QHBoxLayout()
        self.back_btn = QPushButton("🔙 Back")
        self.back_btn.setFixedWidth(60)
        self.back_btn.setStyleSheet("""
            QPushButton {
                background-color: #222;
                color: white;
                font-size: 12px;
                border: 1px solid #00ffcc;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #00ffcc;
                color: black;
            }
        """)
        self.back_btn.clicked.connect(self.go_back)
        back_btn_layout.addWidget(self.back_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addLayout(back_btn_layout)

        # 🎮 Title
        title = QLabel("🍽️ Choose a Recipe")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #00ffcc; margin-top: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # 🧾 Recipe List Box
        recipe_box = QGroupBox("📜 Available Recipes")
        recipe_box.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: #00ffcc;
                border: 2px solid #00ffcc;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 20px; /* Extra padding for title */
            }
        """)
        recipe_layout = QVBoxLayout()
        recipe_layout.setContentsMargins(10, 10, 10, 10)
        recipe_layout.setSpacing(8)

        self.dishes = {
            '🥣 Poha': [
                ('Flattened rice', '50g'),
                ('Onion', '30g'),
                ('Green peas', '20g'),
                ('Oil', '5ml')
            ],
            '🥪 Sandwich': [
                ('Bread slices', '2 pcs'),
                ('Cheese', '20g'),
                ('Tomato', '25g'),
                ('Cucumber', '30g')
            ],
            '🍵 Soup': [
                ('Carrot', '40g'),
                ('Beans', '30g'),
                ('Salt', '5g'),
                ('Water', '250ml')
            ],
            '🥗 Salad': [
                ('Lettuce', '50g'),
                ('Cucumber', '30g'),
                ('Tomato', '40g'),
                ('Olive oil', '10ml')
            ],
            '🍚 Rice Dish': [
                ('Rice', '100g'),
                ('Vegetables', '50g'),
                ('Ghee', '10g'),
                ('Spices', '5g')
            ]
        }

        self.recipe_list = QListWidget()
        self.recipe_list.addItems(self.dishes.keys())
        self.recipe_list.setStyleSheet("""
            QListWidget {
                background-color: #1f1f1f;
                color: white;
                font-size: 14px;
                border: 1px solid #00ffcc;
                border-radius: 6px;
                padding: 6px;
            }
            QListWidget::item:selected {
                background-color: #00ffcc;
                color: black;
                font-weight: bold;
            }
        """)
        self.recipe_list.itemClicked.connect(self.display_ingredients)
        recipe_layout.addWidget(self.recipe_list)
        recipe_box.setLayout(recipe_layout)
        layout.addWidget(recipe_box)

        # 🧾 Ingredient Display
        self.ingredient_display = QTextEdit()
        self.ingredient_display.setReadOnly(True)
        self.ingredient_display.setFixedHeight(120)
        self.ingredient_display.setStyleSheet("""
            QTextEdit {
                background-color: #1f1f1f;
                color: white;
                font-size: 13px;
                border: 1px solid #00ffcc;
                border-radius: 6px;
                padding: 6px;
            }
        """)
        layout.addWidget(self.ingredient_display)

        # ✅ Start Scanning Button
        self.scan_button = QPushButton("🚀 Start Scanning")
        self.scan_button.setStyleSheet("""
            QPushButton {
                background-color: #00ffcc;
                color: black;
                padding: 10px;
                font-size: 15px;
                font-weight: bold;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #00e6b8;
            }
        """)
        self.scan_button.clicked.connect(self.open_scanner)
        layout.addWidget(self.scan_button)

        self.setLayout(layout)

    def display_ingredients(self, item):
        dish = item.text()
        ingredients = self.dishes.get(dish, [])
        text = "\n".join([f"• {name}: {amount}" for name, amount in ingredients])
        self.ingredient_display.setText(text)

    def open_scanner(self):
        selected_item = self.recipe_list.currentItem()
        if selected_item:
            dish_name = selected_item.text()
            ingredients = self.dishes.get(dish_name, [])

            self.scan_window = RecipeNutritionScanner(dish_name, ingredients)
            self.scan_window.show()
            self.hide()

            # Re-show this window after scanner is closed
            self.scan_window.destroyed.connect(self.show)
        else:
            QMessageBox.warning(self, "No Selection", "Please select a recipe first.")

    def reset_scanner_ref(self):
        self.scan_window = None
        self.show()

    def show_again(self):
        self.scan_window = None
        self.show()

    def go_back(self):
        if self.main_menu:
            self.main_menu.show()
        self.close()
