from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from .nutrition_app import NutritionApp

class RecipeScannerWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📋 Recipe Scanner")
        self.setFixedSize(400, 300)
        self.setStyleSheet("background-color: #111; color: white;")

        layout = QVBoxLayout()

        # Inside RecipeScannerWindow.__init__()
        self.dishes = {
            'Poha': [
                ('Flattened rice', '50g'),
                ('Onion', '30g'),
                ('Green peas', '20g'),
                ('Oil', '5ml')
            ],
            'Sandwich': [
                ('Bread slices', '2 pcs'),
                ('Cheese', '20g'),
                ('Tomato', '25g'),
                ('Cucumber', '30g')
            ]
        }

        self.ingredient_list = QListWidget()
        for dish in self.dishes.keys():
            self.ingredient_list.addItem(dish)

        self.ingredient_list.itemClicked.connect(self.open_dish_details)
        layout.addWidget(self.ingredient_list)  # Add this to your main layout in RecipeScannerWindow

        title = QLabel("🧾 Select Recipe Type to Scan")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #00ffcc; margin: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self.ingredient_list = QListWidget()
        self.ingredient_list.addItems([
            "🥗 Salad Ingredients",
            "🍛 Poha Ingredients",
            "🍲 Soup Ingredients",
            "🍞 Sandwich Ingredients",
            "🍚 Rice Dish Ingredients"
        ])
        self.ingredient_list.setStyleSheet("""
            QListWidget {
                background-color: #222;
                color: white;
                font-size: 14px;
                padding: 8px;
                border: 2px solid #00ffcc;
                border-radius: 8px;
            }
        """)
        layout.addWidget(self.ingredient_list)

        btn = QPushButton("✅ Start Scanning")
        btn.setStyleSheet("""
            QPushButton {
                background-color: #00ffcc;
                color: black;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #00e6b8;
            }
        """)
        btn.clicked.connect(self.start_scan)
        layout.addWidget(btn)

        self.setLayout(layout)

    def start_scan(self):
        selected = self.ingredient_list.currentItem()
        if selected:
            QMessageBox.information(self, "Scanning", f"Start scanning for: {selected.text()}")
        else:
            QMessageBox.warning(self, "No Selection", "Please select a recipe type first.")

    def open_dish_details(self, item):
        dish_name = item.text()
        ingredients = self.dishes.get(dish_name, [])
        self.details_window = DishDetailWindow(dish_name, ingredients, self.open_scanner)
        self.details_window.show()

    def open_scanner(self):
        self.scan_window = NutritionApp()  # Replace with your real scanner window class
        self.scan_window.show()

class DishDetailWindow(QWidget):
    def __init__(self, dish_name, ingredients, scan_callback):
        super().__init__()
        self.setWindowTitle(f"{dish_name} Ingredients")
        layout = QVBoxLayout()

        for item, weight in ingredients:
            layout.addWidget(QLabel(f"{item}: {weight}"))

        scan_button = QPushButton("Start Scanning")
        scan_button.clicked.connect(scan_callback)
        layout.addWidget(scan_button)

        self.setLayout(layout)

