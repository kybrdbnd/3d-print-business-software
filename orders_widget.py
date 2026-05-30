import csv
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPainter, QPageSize, QPdfWriter
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QFileDialog,
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
from constants import ORDER_STATUSES, DEFAULT_ORDER_STATUS



class OrdersWidget(QWidget):
    def __init__(self, send_grid=None, parent=None):
        super().__init__(parent)
        self.send_grid = send_grid
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

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by invoice # or email...")
        self.search_input.setMinimumWidth(320)
        self.search_input.textChanged.connect(self.on_search_text_changed)
        header_layout.addWidget(self.search_input)

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

        self.send_email_button = QToolButton()
        self.send_email_button.setText("Send Email")
        self.send_email_button.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay)
        )
        self.send_email_button.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon
        )
        self.send_email_button.clicked.connect(self.on_send_email_clicked)
        header_layout.addWidget(self.send_email_button)

        self.generate_button = QToolButton()
        self.generate_button.setText("Generate Invoice")
        self.generate_button.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)
        )
        self.generate_button.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon
        )
        self.generate_button.clicked.connect(self.on_generate_invoice_clicked)
        header_layout.addWidget(self.generate_button)

        self.export_button = QToolButton()
        self.export_button.setText("Export Orders")
        self.export_button.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton)
        )
        self.export_button.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon
        )
        self.export_button.clicked.connect(self.on_export_orders_clicked)
        header_layout.addWidget(self.export_button)

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
        self.table.setColumnWidth(3, 320)  # Email column
        self.table.setColumnWidth(4, 220)  # Phone column
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

    def load_orders(self, query=None):
        self.table.setRowCount(0)
        self.table.setSortingEnabled(False)
        orders = list(get_all_orders())
        if query:
            query_lower = query.strip().lower()
            orders = [
                order
                for order in orders
                if query_lower in order["invoice_number"].lower()
                or query_lower in order["email_id"].lower()
            ]
        self.table.setRowCount(len(orders))
        for row, order in enumerate(orders):
            self.table.setItem(row, 0, QTableWidgetItem(order["invoice_number"]))
            self.table.setItem(row, 1, QTableWidgetItem(order["order_name"]))
            self.table.setItem(row, 2, QTableWidgetItem(f"₹ {order['total_cost']:.2f}"))
            self.table.setItem(row, 3, QTableWidgetItem(order["email_id"]))
            self.table.setItem(row, 4, QTableWidgetItem(order["phone_number"]))
            status = order["status"] if "status" in order.keys() else "New"
            self.table.setItem(row, 5, QTableWidgetItem(status))
        self.table.setSortingEnabled(True)

    def on_search_text_changed(self, text):
        self.load_orders(text)

    def on_export_orders_clicked(self):
        default_name = datetime.now().strftime("orders_export_%Y%m%d_%H%M%S.csv")
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Orders to CSV",
            default_name,
            "CSV Files (*.csv)",
        )
        if not path:
            return
        if not path.lower().endswith(".csv"):
            path += ".csv"

        orders = get_all_orders()
        headers = [
            "Invoice #",
            "Order Name",
            "Total Cost (₹)",
            "Email",
            "Phone",
            "Status",
            "Created At",
            "Updated At",
        ]
        try:
            with open(path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(headers)
                for order in orders:
                    writer.writerow(
                        [
                            order["invoice_number"],
                            order["order_name"],
                            f"{order['total_cost']:.2f}",
                            order["email_id"],
                            order["phone_number"],
                            order["status"],
                            order["created_at"],
                            order["updated_at"],
                        ]
                    )
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Could not export orders:\n{exc}",
            )
            return

        QMessageBox.information(
            self,
            "Export Complete",
            f"Orders exported successfully to:\n{path}",
        )

    def on_send_email_clicked(self):
        if self.send_grid is None:
            QMessageBox.warning(
                self,
                "Send Email",
                "SendGrid client is not configured.",
            )
            return

        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(
                self,
                "Send Email",
                "Please select an order to send email for.",
            )
            return

        row = self.table.currentRow()
        invoice_number = self.table.item(row, 0).text()
        selected_order = get_order_invoice_number(invoice_number)
        if selected_order is None:
            QMessageBox.warning(
                self,
                "Send Email",
                "Selected order could not be found.",
            )
            return

        order_items = get_order_items(selected_order["id"])
        items = [
            {
                "item_name": item["item_name"],
                "quantity": item["quantity"],
                "price_per_unit": item["price_per_unit"],
            }
            for item in order_items
        ]
        invoice_items = [
            (item["item_name"], item["quantity"], item["price_per_unit"])
            for item in order_items
        ]
        pdf_path = self._generate_invoice_pdf(
            invoice_number,
            selected_order["order_name"],
            selected_order["total_cost"],
            selected_order["email_id"],
            selected_order["phone_number"],
            selected_order["status"] if "status" in selected_order.keys() else "New",
            invoice_items,
        )
        context = {
            "invoice_number": selected_order["invoice_number"],
            "order_name": selected_order["order_name"],
            "total_cost": f"{selected_order['total_cost']:.2f}",
            "email_id": selected_order["email_id"],
            "phone_number": selected_order["phone_number"],
            "status": selected_order["status"] if "status" in selected_order.keys() else "New",
            "items": items,
        }
        try:
            self.send_grid.send_email(
                to_email=selected_order["email_id"],
                subject=f"Order Received: {invoice_number}",
                template_name="order_received.html",
                context=context,
                attachments=[
                    {
                        "path": pdf_path,
                        "filename": f"invoice_{invoice_number}.pdf",
                        "mime_type": "application/pdf",
                    }
                ],
            )
            QMessageBox.information(
                self,
                "Email Sent",
                f"Order email sent to {selected_order['email_id']}.",
            )
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Send Email Failed",
                f"Failed to send email:\n{exc}",
            )

    def on_generate_invoice_clicked(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(
                self,
                "Generate Invoice",
                "Please select an order to generate an invoice for.",
            )
            return

        row = self.table.currentRow()
        invoice_number = self.table.item(row, 0).text()
        selected_order = get_order_invoice_number(invoice_number)
        if selected_order is None:
            QMessageBox.warning(
                self,
                "Generate Invoice",
                "Selected order could not be found.",
            )
            return

        order_items = get_order_items(selected_order["id"])
        items = [
            (item["item_name"], item["quantity"], item["price_per_unit"])
            for item in order_items
        ]
        pdf_path = self._generate_invoice_pdf(
            invoice_number,
            selected_order["order_name"],
            selected_order["total_cost"],
            selected_order["email_id"],
            selected_order["phone_number"],
            selected_order["status"] if "status" in selected_order.keys() else "New",
            items,
        )
        QMessageBox.information(
            self,
            "Invoice Generated",
            f"Invoice generated successfully:\n{pdf_path}",
        )

    def _show_order_form(
        self,
        title,
        order_name="",
        email_id="",
        phone_number="",
        order_status=DEFAULT_ORDER_STATUS,
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
        email_input.setMinimumWidth(320)
        phone_input = QLineEdit(phone_number)
        phone_input.setMinimumWidth(220)

        if disable_invoice:
            invoice_label = QLabel(invoice_number)
            form.addRow("Invoice Number:", invoice_label)

        form.addRow("Order Name:", order_name_input)
        form.addRow("Email ID:", email_input)
        form.addRow("Phone Number:", phone_input)

        status_input = QComboBox()
        status_input.addItems(ORDER_STATUSES)
        status_input.setCurrentText(order_status)
        form.addRow("Status:", status_input)

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
            status_input.currentText(),
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

        order_name, total_cost, email_id, phone_number, status, items = result
        invoice_number = add_order(
            order_name, total_cost, email_id, phone_number, status, items
        )
        pdf_path = self._generate_invoice_pdf(
            invoice_number,
            order_name,
            total_cost,
            email_id,
            phone_number,
            status,
            items,
        )
        QMessageBox.information(
            self,
            "Order Created",
            f"Order created successfully with invoice number {invoice_number}.\nInvoice PDF saved to:\n{pdf_path}",
        )
        self.load_orders()

    def _generate_invoice_pdf(
        self,
        invoice_number,
        order_name,
        total_cost,
        email_id,
        phone_number,
        status,
        items,
    ):
        file_name = f"invoice/invoice_{invoice_number}.pdf"
        output_path = Path.cwd() / file_name
        output_path.parent.mkdir(parents=True, exist_ok=True)

        writer = QPdfWriter(str(output_path))
        writer.setPageSize(QPageSize(QPageSize.A4))
        writer.setResolution(300)

        painter = QPainter(writer)
        title_font = QFont("Helvetica", 28, QFont.Weight.Bold)
        heading_font = QFont("Helvetica", 12, QFont.Weight.Bold)
        normal_font = QFont("Helvetica", 10)

        margin = 50
        x_right = 450
        line_height = 30
        y = margin

        painter.setFont(title_font)
        painter.drawText(margin, y, "Invoice")
        y += 50

        painter.setFont(normal_font)
        painter.drawText(margin, y, f"Invoice #: {invoice_number}")
        painter.drawText(
            x_right, y, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} "
        )
        y += line_height
        painter.drawText(margin, y, f"Order Name: {order_name}")
        y += line_height
        painter.drawText(margin, y, f"Email: {email_id}")
        y += line_height
        painter.drawText(margin, y, f"Phone: {phone_number}")
        y += line_height
        painter.drawText(margin, y, f"Status: {status}")
        y += line_height * 1.5

        painter.setFont(heading_font)
        painter.drawText(margin, y, "Item")
        painter.drawText(margin + 260, y, "Quantity")
        painter.drawText(margin + 360, y, "Price / g")
        painter.drawText(margin + 460, y, "Cost")
        y += line_height

        painter.setPen(Qt.GlobalColor.black)
        painter.drawLine(margin, y - 10, x_right + 80, y - 10)
        y += 10
        painter.setFont(normal_font)

        page_height = writer.pageLayout().fullRect().height()
        bottom_margin = 70

        for item_name, quantity, price_per_unit in items:
            if y > page_height - bottom_margin:
                writer.newPage()
                painter.setFont(normal_font)
                y = margin + 20

            cost = quantity * price_per_unit
            painter.drawText(margin, y, item_name)
            painter.drawText(margin + 260, y, str(quantity))
            painter.drawText(margin + 360, y, f"{price_per_unit:.2f}")
            painter.drawText(margin + 460, y, f"{cost:.2f}")
            y += line_height

        y += line_height
        if y > page_height - bottom_margin:
            writer.newPage()
            painter.setFont(heading_font)
            y = margin + 20

        painter.setFont(heading_font)
        painter.drawText(margin, y, f"Total Cost: ₹ {total_cost:.2f}")

        painter.end()
        return str(output_path)

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

        current_status = (
            get_selected_order["status"]
            if "status" in get_selected_order.keys()
            else DEFAULT_ORDER_STATUS
        )
        result = self._show_order_form(
            "Edit Order",
            current_order_name,
            current_email,
            current_phone,
            current_status,
            items,
            disable_invoice=True,
            invoice_number=current_invoice,
        )
        if not result:
            return

        order_name, total_cost, email_id, phone_number, status, items = result
        update_order(
            get_selected_order["id"],
            current_invoice,
            order_name,
            total_cost,
            email_id,
            phone_number,
            status,
            items,
        )
        self.load_orders()
