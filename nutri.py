import sys
import cv2
import numpy as np
from pyzbar.pyzbar import decode
import requests
import threading
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QTextEdit, QVBoxLayout,
    QHBoxLayout, QFrame, QMessageBox, QPushButton, QLineEdit
)
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QInputDialog

# Ingredient flags
UNHEALTHY_INGREDIENTS = ['palm oil', 'high-fructose corn syrup', 'hydrogenated oil']
ALLERGENS = ['gluten', 'milk', 'soy', 'egg', 'nuts', 'peanuts', 'wheat']
SUSPICIOUS_ADDITIVES = ['e102', 'e110', 'e120', 'e124', 'e250', 'e621']

def analyze_ingredients(ingredient_text):
    ingredients = ingredient_text.lower().replace("(", "").replace(")", "").replace(".", "").split(",")
    flagged = {"unhealthy": [], "allergens": [], "suspicious": [], "natural": []}
    for ing in ingredients:
        ing = ing.strip()
        if any(x in ing for x in UNHEALTHY_INGREDIENTS):
            flagged["unhealthy"].append(ing)
        elif any(x in ing for x in ALLERGENS):
            flagged["allergens"].append(ing)
        elif any(x in ing for x in SUSPICIOUS_ADDITIVES):
            flagged["suspicious"].append(ing)
        elif ing != '':
            flagged["natural"].append(ing)
    return flagged

def calculate_health_score(ingredient_analysis):
    score = 100
    score -= len(ingredient_analysis.get("unhealthy", [])) * 30
    score -= len(ingredient_analysis.get("allergens", [])) * 20
    score -= len(ingredient_analysis.get("suspicious", [])) * 10
    return max(0, min(score, 100))

def get_nutrition_from_api(barcode):
    try:
        res = requests.get(f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json", timeout=5)
        data = res.json()
        if data.get('status') != 1:
            return {"name": "Product not found", "calories": "N/A", "protein": "N/A", "fat": "N/A",
                    "ingredients": "N/A", "ingredient_analysis": {}}

        product = data['product']
        name = product.get('product_name', 'Unknown Product')
        nutriments = product.get('nutriments', {})
        calories = nutriments.get('energy-kcal_100g', 'N/A')
        protein = nutriments.get('proteins_100g', 'N/A')
        fat = nutriments.get('fat_100g', 'N/A')
        ingredients_text = product.get('ingredients_text', 'N/A')
        ingredient_analysis = analyze_ingredients(ingredients_text)

        return {
            "name": name,
            "calories": f"{calories} kcal",
            "protein": f"{protein} g",
            "fat": f"{fat} g",
            "ingredients": ingredients_text,
            "ingredient_analysis": ingredient_analysis
        }

    except:
        return {"name": "Error fetching data", "calories": "N/A", "protein": "N/A", "fat": "N/A",
                "ingredients": "N/A", "ingredient_analysis": {}}

def draw_circular_meter(frame, box_points, score):
    pts = np.array([(point.x, point.y) for point in box_points], np.int32)
    x, y, w, h = cv2.boundingRect(pts)
    center = (x + w // 2, y + h // 2)
    radius = max(w, h) // 2 + 15

    if score > 75:
        color = (0, 255, 0)
    elif score > 50:
        color = (0, 255, 255)
    elif score > 25:
        color = (0, 165, 255)
    else:
        color = (0, 0, 255)

    thickness = 6
    start_angle = -90
    end_angle = int((score / 100) * 360) - 90

    cv2.circle(frame, center, radius, (50, 50, 50), thickness)
    cv2.ellipse(frame, center, (radius, radius), 0, start_angle, end_angle, color, thickness)
    cv2.putText(frame, f"{score}%", (center[0] - 25, center[1] + 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

def safe_float(val):
    try:
        return float(str(val).split()[0])
    except:
        return 0.0

class Cart:
    def __init__(self):
        self.items = []

    def add_item(self, product):
        self.items.append(product)

    def total_calories(self):
        return sum(safe_float(item.get('calories', 0)) for item in self.items)

    def total_fat(self):
        return sum(safe_float(item.get('fat', 0)) for item in self.items)

    def total_protein(self):
        return sum(safe_float(item.get('protein', 0)) for item in self.items)

    def total_health_score(self):
        return sum(calculate_health_score(item['ingredient_analysis']) for item in self.items)

    def challenge_1500_kcal(self):
        return self.total_calories() <= 1500

    def challenge_protein_rich(self):
        return self.total_protein() >= 60 and self.total_fat() <= 50

    def game_score(self):
        score = self.total_health_score()
        if self.challenge_1500_kcal():
            score += 50
        if self.challenge_protein_rich():
            score += 30
        return score

    def clear(self):
        self.items = []


# Main App
class NutritionApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Healthy Cart Game")
        self.setStyleSheet("background-color: #121212; color: white;")
        self.setFixedSize(1080, 520)

        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # 🎥 Video Preview Panel
        self.video_label = QLabel()
        self.video_label.setFixedSize(640, 480)
        self.video_label.setStyleSheet("border: 3px solid #00ffcc; border-radius: 10px;")
        main_layout.addWidget(self.video_label)

        # 🧾 Info Panel
        info_layout = QVBoxLayout()
        main_layout.addLayout(info_layout)

        title = QLabel("🧠 Nutrition Analyzer")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #00ffcc;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_layout.addWidget(title)

        def styled_label(text, bold=False):
            return f"font-size: 14px; {'font-weight: bold;' if bold else ''} margin-top: 4px; color: #ffffff;"

        self.name_label = QLabel("Product Name: ")
        self.name_label.setStyleSheet(styled_label("", True))
        info_layout.addWidget(self.name_label)

        self.calories_label = QLabel("Calories: ")
        self.calories_label.setStyleSheet(styled_label(""))
        info_layout.addWidget(self.calories_label)

        self.protein_label = QLabel("Protein: ")
        self.protein_label.setStyleSheet(styled_label(""))
        info_layout.addWidget(self.protein_label)

        self.fat_label = QLabel("Fat: ")
        self.fat_label.setStyleSheet(styled_label(""))
        info_layout.addWidget(self.fat_label)

        self.ingredients_title = QLabel("🧪 Ingredients")
        self.ingredients_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #00ffcc; margin-top: 10px;")
        info_layout.addWidget(self.ingredients_title)
        

        self.ingredients_text = QTextEdit()
        self.ingredients_text.setReadOnly(True)
        self.ingredients_text.setStyleSheet("""
            background-color: #1f1f1f;
            color: white;
            border: 2px solid #00ffcc;
            border-radius: 8px;
            font-size: 13px;
        """)
        self.ingredients_text.setFixedHeight(180)
        info_layout.addWidget(self.ingredients_text)

        def style_button():
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

        # 🏋️‍♂️ Weight input field
        self.weight_label = QLabel("Weight (g):")
        self.weight_label.setStyleSheet("font-size: 13px; color: white;")
        self.weight_input = QLineEdit()
        self.weight_input.setText("100")  # Default 100g
        self.weight_input.setFixedWidth(60)
        self.weight_input.setStyleSheet("background-color: #1f1f1f; color: white; padding: 4px;")

        weight_layout = QHBoxLayout()
        weight_layout.addWidget(self.weight_label)
        weight_layout.addWidget(self.weight_input)
        info_layout.addLayout(weight_layout)

        self.add_cart_btn = QPushButton("➕ Add to Cart")
        self.add_cart_btn.setStyleSheet(style_button())
        self.add_cart_btn.clicked.connect(self.add_to_cart)
        info_layout.addWidget(self.add_cart_btn)

        self.finish_game_btn = QPushButton("🏁 Finish Game")
        self.finish_game_btn.setStyleSheet(style_button())
        self.finish_game_btn.clicked.connect(self.finish_game)
        info_layout.addWidget(self.finish_game_btn)

        self.status_label = QLabel("💡 Scan a product to begin")
        self.status_label.setStyleSheet("color: #cccccc; font-style: italic; margin-top: 10px;")
        info_layout.addWidget(self.status_label)

        # 🎥 Video Capture Setup
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            QMessageBox.critical(self, "Camera Error", "Could not open webcam.")
            sys.exit(1)

        self.last_scanned = ""
        self.product_info = {}
        self.cart = Cart()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        barcodes = decode(frame)
        for barcode in barcodes:
            barcode_data = barcode.data.decode('utf-8')
            points = barcode.polygon

            if barcode_data == self.last_scanned and self.product_info:
                score = calculate_health_score(self.product_info.get("ingredient_analysis", {}))
            else:
                score = 0

            draw_circular_meter(frame, points, score)

            if barcode_data != self.last_scanned:
                self.last_scanned = barcode_data
                threading.Thread(target=self.fetch_product_info, args=(barcode_data,), daemon=True).start()
            break

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        self.video_label.setPixmap(QPixmap.fromImage(qimg))

    def fetch_product_info(self, barcode_data):
        info = get_nutrition_from_api(barcode_data)
        self.product_info = info
        QTimer.singleShot(0, self.update_info_panel)

    def update_info_panel(self):
        info = self.product_info
        self.name_label.setText(f"Product Name: {info['name']}")
        self.calories_label.setText(f"Calories: {info['calories']}")
        self.protein_label.setText(f"Protein: {info['protein']}")
        self.fat_label.setText(f"Fat: {info['fat']}")

        self.ingredients_text.clear()
        self.ingredients_text.append(info['ingredients'] + "\n")

        ia = info.get("ingredient_analysis", {})
        if ia:
            if ia['unhealthy']:
                self.ingredients_text.append(f"<span style='color:red;'>❌ Unhealthy: {', '.join(ia['unhealthy'])}</span>")
            if ia['allergens']:
                self.ingredients_text.append(f"<span style='color:orange;'>⚠️ Allergens: {', '.join(ia['allergens'])}</span>")
            if ia['suspicious']:
                self.ingredients_text.append(f"<span style='color:#ffaa00;'>🧪 Suspicious: {', '.join(ia['suspicious'])}</span>")
            if ia['natural']:
                self.ingredients_text.append(f"<span style='color:lightgreen;'>✅ Natural: {', '.join(ia['natural'][:5])}...</span>")


    def add_to_cart(self):
        if self.product_info and self.product_info['name'] != "Product not found":
            try:
                weight = float(self.weight_input.text())
            except ValueError:
                self.status_label.setText("❌ Invalid weight entered")
                return

            factor = weight / 100.0  # because values are per 100g
            scaled_product = self.product_info.copy()
            scaled_product['calories'] = f"{safe_float(self.product_info['calories']) * factor:.2f} kcal"
            scaled_product['fat'] = f"{safe_float(self.product_info['fat']) * factor:.2f} g"
            scaled_product['protein'] = f"{safe_float(self.product_info['protein']) * factor:.2f} g"

            self.cart.add_item(scaled_product)
            self.status_label.setText(f"✅ Added {weight}g of {self.product_info['name']} to cart")



    def finish_game(self):
        score = self.cart.game_score()
        cal = self.cart.total_calories()
        fat = self.cart.total_fat()
        protein = self.cart.total_protein()

        challenge1 = self.cart.challenge_1500_kcal()
        challenge2 = self.cart.challenge_protein_rich()

        def restart_game():
            self.cart.clear()
            self.status_label.setText("🛒 Cart Cleared. Play Again!")
            self.last_scanned = ""  # 🔁 Reset last scanned

        self.game_over_window = GameOverWindow(
            score, cal, fat, protein,
            challenge1, challenge2,
            on_play_again=restart_game
        )
        self.game_over_window.show()


    def closeEvent(self, event):
        self.cap.release()
        event.accept()

class MainMenu(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Healthy Cart Challenge")
        self.setFixedSize(500, 400)
        self.setStyleSheet("background-color: #111; color: white;")

        self.game_window = NutritionApp()

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


class GameOverWindow(QWidget):
    def __init__(self, score, calories, fat, protein, challenge1, challenge2, on_play_again):
        super().__init__()
        self.setWindowTitle("🎉 Game Over")
        self.setFixedSize(500, 400)
        self.setStyleSheet("background-color: #000; color: white;")

        layout = QVBoxLayout()

        title = QLabel("🏁 Game Summary")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #00ffcc;")
        layout.addWidget(title)

        stats = f"""
        🎯 Final Score: {score}<br>
        🔥 Calories: {calories:.1f} kcal<br>
        🧈 Fat: {fat:.1f} g<br>
        🥩 Protein: {protein:.1f} g<br><br>
        {"✅" if challenge1 else "❌"} Challenge 1: Under 1500 kcal<br>
        {"✅" if challenge2 else "❌"} Challenge 2: High Protein, Low Fat
        """
        stats_label = QLabel(stats)
        stats_label.setStyleSheet("font-size: 16px;")
        stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats_label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(stats_label)

        # Buttons Layout
        buttons_layout = QHBoxLayout()

        # Play Again Button
        play_btn = QPushButton("🔄 Play Again")
        play_btn.setStyleSheet("""
            QPushButton {
                background-color: #00ffcc;
                color: black;
                font-size: 16px;
                padding: 10px;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #00e6b8;
            }
        """)
        play_btn.clicked.connect(self.close)
        play_btn.clicked.connect(on_play_again)
        buttons_layout.addWidget(play_btn)

        # Quit Button
        quit_btn = QPushButton("❌ Quit")
        quit_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff4d4d;
                color: white;
                font-size: 16px;
                padding: 10px;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #e60000;
            }
        """)
        quit_btn.clicked.connect(QApplication.instance().quit)
        buttons_layout.addWidget(quit_btn)

        layout.addLayout(buttons_layout)
        self.setLayout(layout)




if __name__ == "__main__":
    app = QApplication(sys.argv)
    menu = MainMenu()
    menu.show()
    sys.exit(app.exec())

