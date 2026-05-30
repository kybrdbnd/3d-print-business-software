from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QStyle,
)

from inventory_db import get_all_items
from orders_db import (
    add_order,
    get_all_orders,
    get_order_invoice_number,
    get_order_items,
    update_order,
)


class OrdersWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Orders")
        self.setStyleSheet(
            "QWidget { background: #121212; color: #e0e0e0; }"
            "QTableWidget { background: #1c1c1c; color: #e0e0e0; gridline-color: #333; }"
            "QTableWidget::item:selected { background: #094771; color: #ffffff; }"
            "QHeaderView::section { background: #202020; color: #e0e0e0; border: 1px solid #333; }"
            "QToolButton { background: #1f1f1f; color: #e0e0e0; border: 1px solid #3c3c3c; padding: 4px 10px; border-radius: 4px; }"
            "QToolButton:hover { background: #2a2a2a; }"
        )
        self.setup_ui()
        self.setMinimumWidth(1000)

    def setup_ui(self):
        main_layout = QVBoxLayout()

        header_layout = QHBoxLayout()
        header_label = QLabel("Orders")
        header_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(header_label)
        header_layout.addStretch()

        self.add_button = QToolButton()
        self.add_button.setText("Add Order")
        self.add_button.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogNewFolder)
        )
        self.add_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.add_button.clicked.connect(self.on_add_order_clicked)

        self.edit_button = QToolButton()
        self.edit_button.setText("Edit Order")
        self.edit_button.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogContentsView)
        )
        self.edit_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.edit_button.clicked.connect(self.on_edit_order_clicked)

        header_layout.addWidget(self.add_button)
        header_layout.addWidget(self.edit_button)

        # Table without checkbox column
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Invoice #", "Order Name", "Total Cost (₹)", "Email", "Phone", "Status"]
        )
        self.table.setStyleSheet(
            "QTableWidget { background: #1c1c1c; color: #e0e0e0; border: 1px solid #999; border-radius: 4px; }"
            "QHeaderView::section { background-color: #2d2d2d; color: #e0e0e0; border: 1px solid #333; }"
            "QTableCornerButton::section { background-color: #2d2d2d; border: 1px solid #333; }"
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        # Set minimum widths for email and phone columns to prevent truncation
        self.table.setColumnWidth(3, 250)  # Email column
        self.table.setColumnWidth(4, 150)  # Phone column
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        self.table.setSortingEnabled(True)
        try:
            self.table.horizontalHeader().setSectionsClickable(True)
        except Exception:
            pass

        main_layout.addLayout(header_layout)
        main_layout.addWidget(self.table)
        self.setLayout(main_layout)

        self.load_orders()

    def load_orders(self):
        self.table.setRowCount(0)
        self.table.setSortingEnabled(False)
        orders = list(get_all_orders())
        self.table.setRowCount(len(orders))
        for row, order in enumerate(orders):
            self.table.setItem(row, 0, QTableWidgetItem(order["invoice_number"]))
            self.table.setItem(row, 1, QTableWidgetItem(order["order_name"]))
            self.table.setItem(row, 2, QTableWidgetItem(f"₹ {order['total_cost']:.2f}"))
            self.table.setItem(row, 3, QTableWidgetItem(order["email_id"]))
            self.table.setItem(row, 4, QTableWidgetItem(order["phone_number"]))
            self.table.setItem(row, 5, QTableWidgetItem("Completed"))
        self.table.setSortingEnabled(True)

    def _show_order_form(
        self,
        title,
        order_name="",
        email_id="",
        phone_number="",
        items=None,
        disable_invoice=False,
        invoice_number="",
    ):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setMinimumWidth(800)

        layout = QVBoxLayout(dialog)

        form = QFormLayout()
        order_name_input = QLineEdit(order_name)
        email_input = QLineEdit(email_id)
        phone_input = QLineEdit(phone_number)

        if disable_invoice:
            invoice_label = QLabel(invoice_number)
            form.addRow("Invoice Number:", invoice_label)

        form.addRow("Order Name:", order_name_input)
        form.addRow("Email ID:", email_input)
        form.addRow("Phone Number:", phone_input)

        layout.addLayout(form)

        items_header = QLabel("Order Items")
        items_header.setStyleSheet("font-weight: bold; margin-top: 12px;")
        layout.addWidget(items_header)

        self.order_items_table = QTableWidget(0, 4)
        self.order_items_table.setHorizontalHeaderLabels(
            ["Item", "Quantity", "Price / g", "Cost"]
        )
        self.order_items_table.horizontalHeader().setStretchLastSection(True)
        self.order_items_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.order_items_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.order_items_table.setColumnWidth(0, 220)
        self.order_items_table.setColumnWidth(1, 100)
        self.order_items_table.setColumnWidth(2, 120)
        self.order_items_table.setColumnWidth(3, 120)

        layout.addWidget(self.order_items_table)

        button_layout = QHBoxLayout()
        add_item_button = QPushButton("Add Item")
        add_item_button.clicked.connect(self._add_order_item_row)
        button_layout.addWidget(add_item_button)

        remove_item_button = QPushButton("Remove Item")
        remove_item_button.clicked.connect(self._remove_selected_order_item_row)
        button_layout.addWidget(remove_item_button)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        total_layout = QHBoxLayout()
        self.total_label = QLabel("Total Cost: ₹ 0.00")
        self.total_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        total_layout.addStretch()
        total_layout.addWidget(self.total_label)
        layout.addLayout(total_layout)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        layout.addStretch()
        dialog.setLayout(layout)

        self._load_order_items(items)
        self._refresh_order_total()

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None

        if not order_name_input.text().strip():
            QMessageBox.warning(self, title, "Order name is required.")
            return None
        if not email_input.text().strip():
            QMessageBox.warning(self, title, "Email ID is required.")
            return None
        if not phone_input.text().strip():
            QMessageBox.warning(self, title, "Phone number is required.")
            return None

        items_data = []
        for row in range(self.order_items_table.rowCount()):
            item_combo = self.order_items_table.cellWidget(row, 0)
            qty_widget = self.order_items_table.cellWidget(row, 1)
            price_item = self.order_items_table.item(row, 2)
            if item_combo is None or qty_widget is None or price_item is None:
                continue
            item_name = item_combo.currentText()
            quantity_value = qty_widget.value()
            price_per_unit = float(price_item.text())
            if quantity_value <= 0:
                QMessageBox.warning(self, title, "Quantity must be at least 1.")
                return None
            items_data.append((item_name, quantity_value, price_per_unit))

        if not items_data:
            QMessageBox.warning(
                self, title, "Please add at least one item to the order."
            )
            return None

        total_cost_value = sum(qty * price for _, qty, price in items_data)

        return (
            order_name_input.text().strip(),
            total_cost_value,
            email_input.text().strip(),
            phone_input.text().strip(),
            items_data,
        )

    def _load_order_items(self, items):
        self.order_items_table.setRowCount(0)
        inventory = get_all_items()
        self._inventory_prices = {
            item["item_name"]: float(item["price"]) for item in inventory
        }
        self._inventory_names = [item["item_name"] for item in inventory]

        if not items:
            return

        for item_name, quantity, price_per_unit in items:
            self._add_order_item_row(item_name, quantity, price_per_unit)

    def _find_order_item_row(self, widget):
        for row in range(self.order_items_table.rowCount()):
            if self.order_items_table.cellWidget(row, 0) is widget:
                return row
            if self.order_items_table.cellWidget(row, 1) is widget:
                return row
        return -1

    def _refresh_order_total(self):
        total = 0.0
        for row in range(self.order_items_table.rowCount()):
            cost_item = self.order_items_table.item(row, 3)
            if cost_item:
                try:
                    total += float(cost_item.text())
                except ValueError:
                    pass
        self.total_label.setText(f"Total Cost: ₹ {total:.2f}")

    def _on_order_item_changed(self):
        sender = self.sender()
        row = self._find_order_item_row(sender)
        if row < 0:
            return

        item_combo = self.order_items_table.cellWidget(row, 0)
        quantity_widget = self.order_items_table.cellWidget(row, 1)
        if item_combo is None or quantity_widget is None:
            return

        selected_item = item_combo.currentText()
        price_value = self._inventory_prices.get(selected_item, 0.0)
        self.order_items_table.setItem(row, 2, QTableWidgetItem(f"{price_value:.2f}"))
        cost_value = quantity_widget.value() * price_value
        self.order_items_table.setItem(row, 3, QTableWidgetItem(f"{cost_value:.2f}"))
        self._refresh_order_total()

    def _add_order_item_row(self, item_name=None, quantity=1, price_per_unit=None):
        row = self.order_items_table.rowCount()
        self.order_items_table.insertRow(row)

        combo = QComboBox()
        combo.addItems(self._inventory_names)
        if item_name and item_name in self._inventory_names:
            combo.setCurrentText(item_name)
        combo.currentTextChanged.connect(self._on_order_item_changed)
        self.order_items_table.setCellWidget(row, 0, combo)

        quantity_widget = QSpinBox()
        quantity_widget.setRange(1, 9999999)
        quantity_widget.setValue(quantity)
        quantity_widget.valueChanged.connect(self._on_order_item_changed)
        self.order_items_table.setCellWidget(row, 1, quantity_widget)

        if price_per_unit is None:
            selected_item = combo.currentText()
            price_per_unit = self._inventory_prices.get(selected_item, 0.0)
        self.order_items_table.setItem(
            row, 2, QTableWidgetItem(f"{price_per_unit:.2f}")
        )
        self.order_items_table.setItem(
            row, 3, QTableWidgetItem(f"{quantity * price_per_unit:.2f}")
        )

        self._refresh_order_total()

    def _remove_selected_order_item_row(self):
        selected_ranges = self.order_items_table.selectedRanges()
        if not selected_ranges:
            QMessageBox.warning(
                self, "Remove Item", "Please select an item row to remove."
            )
            return

        row = selected_ranges[0].topRow()
        self.order_items_table.removeRow(row)
        self._refresh_order_total()

    def on_add_order_clicked(self):
        result = self._show_order_form("Add Order")
        if not result:
            return

        order_name, total_cost, email_id, phone_number, items = result
        invoice_number = add_order(
            order_name, total_cost, email_id, phone_number, items
        )
        QMessageBox.information(
            self,
            "Order Created",
            f"Order created successfully with invoice number {invoice_number}.",
        )
        self.load_orders()

    def on_edit_order_clicked(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Edit Order", "Please select an order to edit.")
            return

        row = self.table.currentRow()
        current_invoice = self.table.item(row, 0).text()
        current_order_name = self.table.item(row, 1).text()
        current_email = self.table.item(row, 3).text()
        current_phone = self.table.item(row, 4).text()
        get_selected_order = get_order_invoice_number(current_invoice)
        order_items = get_order_items(get_selected_order["id"])
        items = [
            (item["item_name"], item["quantity"], item["price_per_unit"])
            for item in order_items
        ]

        result = self._show_order_form(
            "Edit Order",
            current_order_name,
            current_email,
            current_phone,
            items,
            disable_invoice=True,
            invoice_number=current_invoice,
        )
        if not result:
            return

        order_name, total_cost, email_id, phone_number, items = result
        update_order(
            get_selected_order["id"],
            current_invoice,
            order_name,
            total_cost,
            email_id,
            phone_number,
            items,
        )
        self.load_orders()
