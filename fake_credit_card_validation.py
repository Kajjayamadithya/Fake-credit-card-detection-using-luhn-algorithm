import sys
import re
import time
import threading
from flask import Flask, render_template_string
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel, QProgressBar
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import webbrowser

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Credit Card Fraud Dashboard</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    body {
      margin: 0;
      font-family: 'Inter', sans-serif;
      background-color: #1e1e2f;
      color: white;
    }
    .sidebar {
      width: 220px;
      background-color: #2a2a3f;
      height: 100vh;
      padding: 20px;
      position: fixed;
    }
    .sidebar h2 {
      font-size: 18px;
      margin-bottom: 40px;
      color: #00e5ff;
    }
    .sidebar ul {
      list-style: none;
      padding: 0;
    }
    .sidebar ul li {
      margin-bottom: 20px;
      cursor: pointer;
    }
    .main {
      margin-left: 240px;
      padding: 30px;
    }
    .cards {
      display: flex;
      gap: 20px;
      margin-bottom: 30px;
    }
    .card {
      background-color: #2e2e42;
      border-radius: 12px;
      padding: 20px;
      flex: 1;
      text-align: center;
    }
    .card h3 {
      margin: 0;
      color: #00e5ff;
    }
    .chart-container {
      background-color: #2e2e42;
      border-radius: 12px;
      padding: 20px;
      max-width: 600px;
      margin-bottom: 30px;
    }
    .charts-row {
      display: flex;
      flex-wrap: wrap;
      gap: 20px;
    }
    canvas {
      max-width: 100%;
      height: 250px !important;
    }
  </style>
</head>
<body>
  <div class="sidebar">
    <h2>Fraud Dashboard</h2>
    <ul>
      <li>Overview</li>
      <li>Wave Chart</li>
      <li>Pie Chart</li>
      <li>Stats</li>
    </ul>
  </div>
  <div class="main">
    <div class="cards">
      <div class="card">
        <h3>Total Transactions</h3>
        <p>100,000</p>
      </div>
      <div class="card">
        <h3>Frauds Before</h3>
        <p>3,500</p>
      </div>
      <div class="card">
        <h3>Frauds After</h3>
        <p>1,200</p>
      </div>
      <div class="card">
        <h3>Reduction</h3>
        <p>65.7%</p>
      </div>
    </div>
    <div class="charts-row">
      <div class="chart-container">
        <h3>Fraud Detection Over Time</h3>
        <canvas id="lineChart"></canvas>
      </div>
      <div class="chart-container">
        <h3>Fraud Comparison</h3>
        <canvas id="pieChart"></canvas>
      </div>
    </div>
  </div>

  <script>
    const lineCtx = document.getElementById('lineChart').getContext('2d');
    const pieCtx = document.getElementById('pieChart').getContext('2d');

    const days = Array.from({ length: 30 }, (_, i) => `Day ${i + 1}`);
    const before = [120,110,100,130,140,135,128,115,120,140,145,138,120,110,125,132,140,135,130,125,130,128,120,110,118,145,140,132,135,128];
    const after =  [40,38,35,45,48,43,40,42,45,50,48,42,38,37,40,45,50,48,46,44,43,42,40,39,38,47,45,43,42,40];

    new Chart(lineCtx, {
      type: 'line',
      data: {
        labels: days,
        datasets: [
          {
            label: 'Before Luhn',
            data: before,
            borderColor: 'red',
            fill: true,
            backgroundColor: 'rgba(255,0,0,0.1)'
          },
          {
            label: 'After Luhn',
            data: after,
            borderColor: 'green',
            fill: true,
            backgroundColor: 'rgba(0,255,0,0.1)'
          }
        ]
      },
      options: {
        responsive: true,
        scales: {
          y: {
            beginAtZero: true
          }
        }
      }
    });

    new Chart(pieCtx, {
      type: 'pie',
      data: {
        labels: ['Frauds Before Luhn', 'Frauds After Luhn'],
        datasets: [{
          data: [3500, 1200],
          backgroundColor: ['red', 'green']
        }]
      },
      options: {
        responsive: true
      }
    });
  </script>
</body>
</html>
"""
@app.route("/")
def dashboard():
    return render_template_string(HTML_TEMPLATE)


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
        self.card_number_input.setPlaceholderText("Enter Credit Card Number")
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
            self.result_label.setText("❌ Invalid card type.")
            self.result_label.setObjectName("invalid")
        elif not is_valid:
            self.result_label.setText("❌ Invalid card (Luhn check failed).")
            self.result_label.setObjectName("invalid")
        else:
            self.result_label.setText(f"✅ Valid {card_type} card")
            self.result_label.setObjectName("valid")
            threading.Thread(target=start_flask_server).start()
        self.result_label.adjustSize()


def start_flask_server():
    threading.Thread(target=lambda: app.run(debug=False, use_reloader=False, port=8050)).start()
    time.sleep(1.5)
    webbrowser.open_new("http://127.0.0.1:8050/")


def main():
    app = QApplication(sys.argv)
    window = CreditCardValidator()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
