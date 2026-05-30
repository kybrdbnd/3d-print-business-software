from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QStyle,
)


class InventoryWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Inventory")
        self.setStyleSheet(
            "QWidget { background: #121212; color: #e0e0e0; }"
            "QTableWidget { background: #1c1c1c; color: #e0e0e0; gridline-color: #333; }"
            "QTableWidget::item:selected { background: #094771; color: #ffffff; }"
            "QHeaderView::section { background: #202020; color: #e0e0e0; border: 1px solid #333; }"
            "QToolButton { background: #1f1f1f; color: #e0e0e0; border: 1px solid #3c3c3c; padding: 4px 10px; border-radius: 4px; }"
            "QToolButton:hover { background: #2a2a2a; }"
        )
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()

        header_layout = QHBoxLayout()
        header_label = QLabel("Current Inventory")
        header_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(header_label)
        header_layout.addStretch()

        self.add_button = QToolButton()
        self.add_button.setText("Add Item")
        self.add_button.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogNewFolder)
        )
        self.add_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.add_button.clicked.connect(self.on_add_item_clicked)

        self.edit_button = QToolButton()
        self.edit_button.setText("Edit Item")
        self.edit_button.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogContentsView)
        )
        self.edit_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.edit_button.clicked.connect(self.on_edit_item_clicked)

        header_layout.addWidget(self.add_button)
        header_layout.addWidget(self.edit_button)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Item", "Quantity", "Price", "Status"])
        self.table.setStyleSheet(
            "QTableWidget { background: #1c1c1c; color: #e0e0e0; border: 1px solid #999; border-radius: 4px; }"
            "QHeaderView::section { background-color: #2d2d2d; color: #e0e0e0; border: 1px solid #333; }"
            "QTableCornerButton::section { background-color: #2d2d2d; border: 1px solid #333; }")
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        main_layout.addLayout(header_layout)
        main_layout.addWidget(self.table)
        self.setLayout(main_layout)

        self.load_sample_inventory()

    def load_sample_inventory(self):
        sample_items = [
            ("PLA Filament", "25", "500", "In Stock"),
            ("Resin", "12", "50", "In Stock"),
            ("Build Plate", "3", "10", "Low"),
        ]

        for item_name, quantity, price, status in sample_items:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(item_name))
            self.table.setItem(row, 1, QTableWidgetItem(quantity))
            self.table.setItem(row, 2, QTableWidgetItem(price))
            self.table.setItem(row, 3, QTableWidgetItem(status))

    def on_add_item_clicked(self):
        print("Add Item button clicked")

    def on_edit_item_clicked(self):
        selected = self.table.selectedItems()
        if selected:
            item_name = selected[0].text()
            print(f"Edit Item clicked for: {item_name}")
        else:
            print("Edit Item clicked with no selection")
