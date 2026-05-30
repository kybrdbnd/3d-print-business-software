import sys
import os
from dotenv import load_dotenv


from PySide6.QtWidgets import QApplication, QHBoxLayout, QPushButton, QWidget

from clients.send_grid import SendGridEmail
from inventory_db import initialize_db
from inventory_widget import InventoryWidget
from orders_db import initialize_orders_db
from orders_widget import OrdersWidget

load_dotenv()

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")


class MainWindow(QWidget):
    def __init__(self, send_grid=None):
        super().__init__()
        self.send_grid = send_grid
        self.setWindowTitle("3D Print Business")
        self.setStyleSheet(
            "QWidget { background: #121212; color: #e0e0e0; }"
            "QPushButton { background: #1f1f1f; color: #e0e0e0; border: 1px solid #3c3c3c; padding: 8px; }"
            "QPushButton:hover { background: #2a2a2a; }"
        )
        self.inventory_window = None
        self.orders_window = None
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout()

        self.orders_button = QPushButton("Orders")
        self.inventory_button = QPushButton("Inventory Management")

        self.orders_button.clicked.connect(self.on_orders_clicked)
        self.inventory_button.clicked.connect(self.on_inventory_clicked)

        layout.addWidget(self.orders_button)
        layout.addWidget(self.inventory_button)

        self.setLayout(layout)

    def on_orders_clicked(self):
        self.orders_window = OrdersWidget(send_grid=self.send_grid)
        self.orders_window.show()

    def on_inventory_clicked(self):
        self.inventory_window = InventoryWidget()
        self.inventory_window.show()


if __name__ == "__main__":
    initialize_db()
    initialize_orders_db()
    app = QApplication(sys.argv)
    send_grid = SendGridEmail(api_key=SENDGRID_API_KEY)
    window = MainWindow(send_grid=send_grid)
    window.show()
    sys.exit(app.exec())
