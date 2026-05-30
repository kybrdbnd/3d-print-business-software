import sys

from PySide6.QtWidgets import QApplication, QHBoxLayout, QPushButton, QWidget

from inventory_widget import InventoryWidget


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("3D Print Business")
        self.setStyleSheet(
            "QWidget { background: #121212; color: #e0e0e0; }"
            "QPushButton { background: #1f1f1f; color: #e0e0e0; border: 1px solid #3c3c3c; padding: 8px; }"
            "QPushButton:hover { background: #2a2a2a; }"
        )
        self.inventory_window = None
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout()

        self.book_order_button = QPushButton("Book a Order")
        self.inventory_button = QPushButton("Inventory")
        self.past_orders_button = QPushButton("Past Orders")

        self.book_order_button.clicked.connect(self.on_book_order_clicked)
        self.inventory_button.clicked.connect(self.on_inventory_clicked)
        self.past_orders_button.clicked.connect(self.on_past_orders_clicked)

        layout.addWidget(self.book_order_button)
        layout.addWidget(self.inventory_button)
        layout.addWidget(self.past_orders_button)

        self.setLayout(layout)

    def on_book_order_clicked(self):
        print("Book a Order clicked")

    def on_inventory_clicked(self):
        self.inventory_window = InventoryWidget()
        self.inventory_window.show()

    def on_past_orders_clicked(self):
        print("Past Orders clicked")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
