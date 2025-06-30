# --- RECIPE NUTRITION SCANNER WINDOW ---

from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QCheckBox, QMessageBox, QLineEdit
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QImage
import cv2, threading

from pyzbar.pyzbar import decode
from core.nutrition import get_nutrition_from_api, calculate_health_score, draw_circular_meter, safe_float
from core.cart import Cart


class RecipeNutritionScanner(QWidget):
    def __init__(self, recipe_name, ingredients):
        super().__init__()
        self.setWindowTitle(f"Recipe Nutrition Scanner - {recipe_name}")
        self.setFixedSize(1080, 520)
        self.setStyleSheet("background-color: #121212; color: white;")

        self.recipe_name = recipe_name
        self.ingredients = ingredients
        self.cart = Cart()
        self.product_info = {}

        main_layout = QHBoxLayout(self)

        # 🎥 Video Area
        self.video_label = QLabel()
        self.video_label.setFixedSize(640, 480)
        self.video_label.setStyleSheet("border: 3px solid #00ffcc; border-radius: 10px;")
        main_layout.addWidget(self.video_label)

        # 📦 Info Area
        info_layout = QVBoxLayout()
        main_layout.addLayout(info_layout)

        title = QLabel(f"📋 Ingredients for {recipe_name}")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #00ffcc;")
        info_layout.addWidget(title)

        self.checkbox_widgets = {}
        for ing_name, weight in ingredients:
            checkbox = QCheckBox(f"{ing_name} - {weight}")
            checkbox.setStyleSheet("font-size: 14px; color: white; margin-bottom: 4px;")
            info_layout.addWidget(checkbox)
            self.checkbox_widgets[ing_name.lower()] = checkbox

        self.nutrition_text = QTextEdit()
        self.nutrition_text.setReadOnly(True)
        self.nutrition_text.setFixedHeight(130)
        self.nutrition_text.setStyleSheet("""
            background-color: #1f1f1f;
            color: white;
            font-size: 13px;
            border: 2px solid #00ffcc;
            border-radius: 8px;
        """)
        info_layout.addWidget(self.nutrition_text)

        # Weight input
        self.weight_input = QLineEdit("100")
        self.weight_input.setStyleSheet("""
            background-color: #2a2a2a;
            color: white;
            padding: 5px;
            font-size: 14px;
            border: 1px solid #00ffcc;
            border-radius: 6px;
        """)
        self.weight_input.setFixedWidth(70)
        weight_layout = QHBoxLayout()
        weight_layout.addWidget(QLabel("Weight (g):"))
        weight_layout.addWidget(self.weight_input)
        info_layout.addLayout(weight_layout)

        self.add_cart_btn = QPushButton("➕ Add to Cart")
        self.add_cart_btn.setStyleSheet(self.button_style())
        self.add_cart_btn.clicked.connect(self.add_to_cart)
        info_layout.addWidget(self.add_cart_btn)

        self.finish_btn = QPushButton("🏁 Finish Recipe")
        self.finish_btn.setStyleSheet(self.button_style())
        self.finish_btn.clicked.connect(self.finish_recipe)
        info_layout.addWidget(self.finish_btn)

        self.status_label = QLabel("💡 Scan ingredients one by one")
        self.status_label.setStyleSheet("color: #cccccc; font-style: italic;")
        info_layout.addWidget(self.status_label)

        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            QMessageBox.critical(self, "Camera Error", "Webcam not accessible")
            self.close()

        self.last_scanned = ""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def button_style(self):
        return """
        QPushButton {
            background-color: #00ffcc;
            color: black;
            padding: 8px 12px;
            font-size: 14px;
            font-weight: bold;
            border-radius: 8px;
        }
        QPushButton:hover {
            background-color: #00e6b8;
        }
        """

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        barcodes = decode(frame)
        for barcode in barcodes:
            barcode_data = barcode.data.decode("utf-8")
            points = barcode.polygon

            if barcode_data != self.last_scanned:
                self.last_scanned = barcode_data
                threading.Thread(target=self.fetch_ingredient_info, args=(barcode_data,), daemon=True).start()

            draw_circular_meter(frame, points, 0)
            break

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        qimg = QImage(frame.data, w, h, ch * w, QImage.Format.Format_RGB888)
        self.video_label.setPixmap(QPixmap.fromImage(qimg))

    def fetch_ingredient_info(self, barcode):
        info = get_nutrition_from_api(barcode)
        self.product_info = info
        name = info.get("name", "").lower()

        matched = None
        for ing in self.checkbox_widgets.keys():
            if ing in name:
                matched = ing
                break

        if matched:
            self.checkbox_widgets[matched].setChecked(True)
            self.status_label.setText(f"✅ Scanned: {info['name']}")
        else:
            self.status_label.setText(f"❌ Unknown item: {info['name']}")

        self.update_info_panel(info)

    def update_info_panel(self, info):
        self.nutrition_text.clear()
        self.nutrition_text.append(f"📦 {info.get('name', '')}")
        self.nutrition_text.append(f"🔥 Calories: {info.get('calories', 'N/A')}")
        self.nutrition_text.append(f"🍗 Protein: {info.get('protein', 'N/A')}")
        self.nutrition_text.append(f"🧈 Fat: {info.get('fat', 'N/A')}")
        self.nutrition_text.append(f"\n{info.get('ingredients', '')}")

    def add_to_cart(self):
        if self.product_info.get("name") == "Product not found":
            return

        try:
            weight = float(self.weight_input.text())
        except ValueError:
            self.status_label.setText("❌ Invalid weight")
            return

        factor = weight / 100.0
        scaled = self.product_info.copy()
        scaled['calories'] = f"{safe_float(scaled['calories']) * factor:.2f} kcal"
        scaled['fat'] = f"{safe_float(scaled['fat']) * factor:.2f} g"
        scaled['protein'] = f"{safe_float(scaled['protein']) * factor:.2f} g"

        self.cart.add_item(scaled)
        self.status_label.setText(f"✅ Added {weight}g of {scaled['name']}")

    def finish_recipe(self):
        total = len(self.ingredients)
        scanned = sum(cb.isChecked() for cb in self.checkbox_widgets.values())
        completion = int((scanned / total) * 100) if total > 0 else 0

        cal = self.cart.total_calories()
        fat = self.cart.total_fat()
        protein = self.cart.total_protein()

        self.summary_window = RecipeSummaryWindow(
            self.recipe_name, total, scanned, completion, cal, fat, protein
        )
        self.summary_window.show()

    def closeEvent(self, event):
        self.cap.release()
        event.accept()


# --- RECIPE SUMMARY WINDOW ---

class RecipeSummaryWindow(QWidget):
    def __init__(self, recipe_name, total, scanned, completion, calories, fat, protein):
        super().__init__()
        self.setWindowTitle("🍽️ Recipe Summary")
        self.setFixedSize(500, 400)
        self.setStyleSheet("background-color: #000; color: white;")

        layout = QVBoxLayout()

        title = QLabel(f"📋 Summary for {recipe_name}")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #00ffcc;")
        layout.addWidget(title)

        stats = f"""
        🧮 Total Ingredients: {total}<br>
        ✅ Scanned: {scanned}<br>
        📊 Completion: {completion}%<br><br>
        🔥 Calories: {calories:.1f} kcal<br>
        🧈 Fat: {fat:.1f} g<br>
        🍗 Protein: {protein:.1f} g
        """
        label = QLabel(stats)
        label.setStyleSheet("font-size: 16px;")
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

        close_btn = QPushButton("❌ Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff4d4d;
                color: white;
                font-size: 14px;
                padding: 10px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #e60000;
            }
        """)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setLayout(layout)
