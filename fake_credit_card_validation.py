import sys
import re
import time
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel, QProgressBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
class LuhnCheckThread(QThread):
    progress_updated = pyqtSignal(int)
    validation_done = pyqtSignal(bool, str)
    def __init__(self, card_number):
        super().__init__()
        self.card_number = card_number
    def run(self):
        for i in range(0, 101, 20):  
            time.sleep(0.3)
            self.progress_updated.emit(i)

        is_valid = self.luhn_check(self.card_number)
        card_type = self.get_card_type(self.card_number)
        self.validation_done.emit(is_valid, card_type)

    def luhn_check(self, card_number):
        card_number = card_number.replace(" ", "")  
        if not card_number.isdigit():
            return False

        digits = [int(d) for d in card_number]
        checksum = 0
        is_second = False

        for i in range(len(digits) - 1, -1, -1):
            d = digits[i]
            if is_second:
                d *= 2
                if d > 9:
                    d -= 9
            checksum += d
            is_second = not is_second

        return checksum % 10 == 0

    def get_card_type(self, card_number):
        patterns = {
            "Visa": r"^4[0-9]{12}(?:[0-9]{3})?$",
            "MasterCard": r"^5[1-5][0-9]{14}$|^50[0-9]{14}$",
            "AmEx": r"^3[47][0-9]{13}$",
            "Discover": r"^6(?:011|5[0-9]{2})[0-9]{12}$"
        }
        for card, pattern in patterns.items():
            if re.match(pattern, card_number):
                return card
        return None

class CreditCardValidator(QWidget):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Credit Card Validator")
        self.setGeometry(300, 300, 400, 300)

        layout = QVBoxLayout()

        self.card_number_input = QLineEdit(self)
        self.card_number_input.setPlaceholderText("Enter Credit Card Number (e.g. 4539 1488 0343 6467)")
        layout.addWidget(self.card_number_input)

        self.validate_button = QPushButton("Validate", self)
        self.validate_button.clicked.connect(self.validate_card)
        layout.addWidget(self.validate_button)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False) 
        layout.addWidget(self.progress_bar)

        self.result_label = QLabel("", self)
        self.result_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.result_label)

        self.setLayout(layout)
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                font-family: Arial, sans-serif;
                padding: 20px;
            }
            QLineEdit {
                padding: 10px;
                font-size: 16px;
                border: 2px solid #33ff33;
                border-radius: 5px;
                background-color: #121212;
                color: white;
            }
            QPushButton {
                background-color: #33ff33;
                color: black;
                font-size: 16px;
                padding: 10px 20px;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #28cc28;
            }
            QLabel {
                font-size: 18px;
                padding: 10px;
                text-align: center;
                color: white;
            }
            QLabel#valid {
                color: #33ff33;
            }
            QLabel#invalid {
                color: red;
            }
            QProgressBar {
                border: 2px solid white;
                border-radius: 5px;
                text-align: center;
                color: white;
                background-color: #121212;
            }
            QProgressBar::chunk {
                background-color: #33ff33;
                width: 10px;
            }
        """)

    def validate_card(self):
        card_number = self.card_number_input.text().strip()
        
        if not card_number:
            self.result_label.setText("❌ Please enter a credit card number!")
            self.result_label.setObjectName("invalid")
            return

        
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)

       
        self.thread = LuhnCheckThread(card_number)
        self.thread.progress_updated.connect(self.progress_bar.setValue)
        self.thread.validation_done.connect(self.display_result)
        self.thread.start()

    def display_result(self, is_valid, card_type):
        self.progress_bar.setVisible(False)

        if not card_type:
            self.result_label.setText("❌ Invalid card type. Please check the number format.")
            self.result_label.setObjectName("invalid")
        elif not is_valid:
            self.result_label.setText("❌ Invalid card (Luhn check failed).")
            self.result_label.setObjectName("invalid")
        else:
            self.result_label.setText(f"✅ Valid {card_type} card")
            self.result_label.setObjectName("valid")

        self.result_label.adjustSize()


def main():
    app = QApplication(sys.argv)
    window = CreditCardValidator()
    window.show()
    sys.exit(app.exec_())
if __name__ == "__main__":
    main()
