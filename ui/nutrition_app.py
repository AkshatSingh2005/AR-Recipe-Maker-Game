from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QImage
import cv2, threading

from core.cart import Cart
from core.nutrition import get_nutrition_from_api, calculate_health_score, draw_circular_meter, safe_float

from pyzbar.pyzbar import decode

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

        # 🏋️‍♂️ Weight input field (Improved Design)
        weight_container = QWidget()
        weight_container.setStyleSheet("""
            background-color: #1e1e1e;
            border: 2px solid #00ffcc;
            border-radius: 8px;
            padding: 6px;
        """)
        weight_layout = QHBoxLayout()
        weight_layout.setContentsMargins(8, 2, 8, 2)
        weight_layout.setSpacing(10)

        weight_label = QLabel("Weight (g):")
        weight_label.setStyleSheet("font-size: 14px; color: #ffffff; font-weight: bold;")

        weight_input = QLineEdit()
        weight_input.setText("100")
        weight_input.setFixedWidth(80)
        weight_input.setStyleSheet("""
            background-color: #2a2a2a;
            color: white;
            font-size: 14px;
            padding: 5px;
            border: 1px solid #00ffcc;
            border-radius: 6px;
        """)

        weight_layout.addWidget(weight_label)
        weight_layout.addWidget(weight_input)
        weight_container.setLayout(weight_layout)

        info_layout.addWidget(weight_container)

        # Assign to self (if needed later)
        self.weight_input = weight_input
        self.weight_label = weight_label

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