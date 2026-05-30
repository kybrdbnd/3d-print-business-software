from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator, QIntValidator, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QStyle,
    QComboBox,
)

from constants import FILAMENTS, QUANTITY_THRESHOLD
from inventory_db import add_item, get_all_items, item_exists, update_item, delete_item


class NumericItem(QTableWidgetItem):
    """Table item that sorts numerically based on a stored numeric value."""

    def __init__(self, value):
        # store text for display
        super().__init__(str(value))
        try:
            self._num = float(value)
        except Exception:
            # fallback: try extracting digits
            try:
                self._num = float(str(value).replace(",", ""))
            except Exception:
                self._num = 0.0

    def __lt__(self, other):
        try:
            if isinstance(other, NumericItem):
                return self._num < other._num
            # try compare by numeric value if other has numeric text
            return self._num < float(other.text())
        except Exception:
            return super().__lt__(other)


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
        self.setMinimumWidth(900)

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

        self.delete_button = QToolButton()
        self.delete_button.setText("Delete")
        try:
            self.delete_button.setIcon(
                self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon)
            )
        except Exception:
            # Fallback icon if SP_TrashIcon is not available
            self.delete_button.setIcon(
                self.style().standardIcon(QStyle.StandardPixmap.SP_DialogCloseButton)
            )
        self.delete_button.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon
        )
        self.delete_button.clicked.connect(self.on_delete_item_clicked)

        header_layout.addWidget(self.delete_button)

        # add a checkbox column for bulk selection
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["", "Item", "Material", "Quantity (g)", "Price / g", "Status"]
        )
        self.table.setStyleSheet(
            "QTableWidget { background: #1c1c1c; color: #e0e0e0; border: 1px solid #999; border-radius: 4px; }"
            "QHeaderView::section { background-color: #2d2d2d; color: #e0e0e0; border: 1px solid #333; }"
            "QTableCornerButton::section { background-color: #2d2d2d; border: 1px solid #333; }"
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        # allow multiple rows to be selected for batch operations
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        # add tooltips for material/quantity/price metadata
        try:
            self.table.horizontalHeaderItem(2).setToolTip("Material selected from available filament types.")
            self.table.horizontalHeaderItem(3).setToolTip("Quantity in grams (g)")
            self.table.horizontalHeaderItem(4).setToolTip("Price is per gram")
        except Exception:
            pass

        # enable sorting by clicking headers
        self.table.setSortingEnabled(True)
        try:
            self.table.horizontalHeader().setSectionsClickable(True)
        except Exception:
            pass

        # keyboard shortcut for delete key
        try:
            self.delete_shortcut = QShortcut(QKeySequence("Delete"), self)
            self.delete_shortcut.activated.connect(self.on_delete_item_clicked)
        except Exception:
            pass

        main_layout.addLayout(header_layout)
        main_layout.addWidget(self.table)
        self.setLayout(main_layout)

        self.load_inventory()

    def load_inventory(self):
        self.table.setRowCount(0)
        # disable sorting while populating to avoid items jumping to other rows
        self.table.setSortingEnabled(False)
        items = list(get_all_items())
        self.table.setRowCount(len(items))
        for row, item in enumerate(items):
            # checkbox in first column
            chk = QTableWidgetItem()
            chk.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            chk.setCheckState(Qt.CheckState.Unchecked)
            self.table.setItem(row, 0, chk)
            self.table.setItem(row, 1, QTableWidgetItem(item["item_name"]))
            try:
                material_value = item["material"]
            except Exception:
                material_value = FILAMENTS[0] if FILAMENTS else "PLA"
            self.table.setItem(row, 2, QTableWidgetItem(material_value))
            self.table.setItem(row, 3, NumericItem(item["quantity"]))
            self.table.setItem(row, 4, NumericItem(f"{item['price']:.2f}"))
            # compute status from quantity instead of trusting DB value
            try:
                qty = int(item["quantity"])
            except Exception:
                qty = 0
            status_display = "In Stock" if qty >= QUANTITY_THRESHOLD else "Low"
            self.table.setItem(row, 5, QTableWidgetItem(status_display))
        # re-enable sorting after population
        self.table.setSortingEnabled(True)

    def _make_label_with_info(self, text, tooltip):
        wrapper = QWidget()
        layout = QHBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel(text)
        info_button = QToolButton()
        info_button.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation)
        )
        info_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        info_button.setAutoRaise(True)
        info_button.setToolTip(tooltip)
        layout.addWidget(label)
        layout.addWidget(info_button)
        layout.addStretch()
        return wrapper

    def _show_item_form(
        self,
        title,
        item_name="",
        material=None,
        quantity=1,
        price=0.0,
        disable_name=False,
    ):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)

        form = QFormLayout(dialog)
        name_input = QLineEdit(item_name)
        if disable_name:
            name_input.setDisabled(True)
        quantity_input = QLineEdit(str(quantity))
        quantity_input.setValidator(QIntValidator(0, 9999999, self))
        price_input = QLineEdit(f"{price:.2f}")
        price_input.setValidator(QDoubleValidator(0.0, 9999999.99, 2, self))
        material_combo = QComboBox()
        material_combo.addItems(FILAMENTS)
        if material and material in FILAMENTS:
            material_combo.setCurrentText(material)
        else:
            material_combo.setCurrentIndex(0)

        form.addRow("Item name:", name_input)
        form.addRow("Material:", material_combo)
        form.addRow(
            self._make_label_with_info(
                "Quantity (g):", "Quantity is measured in grams."
            ),
            quantity_input,
        )
        form.addRow(
            self._make_label_with_info(
                "Price per gram:", "Price is entered per gram."
            ),
            price_input,
        )
        # Removed status input from form

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None

        if not name_input.text().strip():
            QMessageBox.warning(self, title, "Item name is required.")
            return None

        try:
            quantity_value = int(quantity_input.text())
            price_value = float(price_input.text())
        except ValueError:
            QMessageBox.warning(
                self, title, "Quantity and price must be valid numbers."
            )
            return None

        return (
            name_input.text().strip(),
            material_combo.currentText(),
            quantity_value,
            price_value,
        )

    def on_add_item_clicked(self):
        result = self._show_item_form("Add Item")
        if not result:
            return

        item_name, material, quantity, price = result
        if item_exists(item_name):
            QMessageBox.warning(
                self,
                "Duplicate Item",
                f"An item with the name '{item_name}' already exists.",
            )
            return
        status = "In Stock" if quantity >= QUANTITY_THRESHOLD else "Low"
        add_item(item_name, quantity, price, status, material)
        self.load_inventory()

    def on_edit_item_clicked(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Edit Item", "Please select an item to edit.")
            return

        row = self.table.currentRow()
        items = get_all_items()
        item_id = items[row]["id"]
        # name now in column 1 (column 0 is the checkbox)
        current_name = self.table.item(row, 1).text()
        current_material = self.table.item(row, 2).text()
        current_quantity = int(self.table.item(row, 3).text())
        current_price = float(self.table.item(row, 4).text())
        # Removed current_status as it is no longer needed

        result = self._show_item_form(
            "Edit Item",
            current_name,
            current_material,
            current_quantity,
            current_price,
            disable_name=True,
        )
        if not result:
            return

        item_name, material, quantity, price = result
        if item_exists(item_name, exclude_id=item_id):
            QMessageBox.warning(
                self,
                "Duplicate Item",
                f"Another item with the name '{item_name}' already exists.",
            )
            return
        status = "In Stock" if quantity >= QUANTITY_THRESHOLD else "Low"
        update_item(item_id, item_name, quantity, price, status, material)
        self.load_inventory()

    def on_delete_item_clicked(self):
        # collect checked rows for bulk-delete
        checked_rows = [
            r
            for r in range(self.table.rowCount())
            if self.table.item(r, 0).checkState() == Qt.CheckState.Checked
        ]

        # fall back to selected rows if no checkboxes used
        if checked_rows:
            sel_rows = checked_rows
        else:
            sel_rows = sorted(
                {idx.row() for idx in self.table.selectionModel().selectedRows()}
            )

        if not sel_rows:
            QMessageBox.warning(
                self,
                "Delete Item",
                "Please select one or more items to delete (either check them or select rows).",
            )
            return

        items = get_all_items()
        ids = [items[r]["id"] for r in sel_rows]
        names = [self.table.item(r, 1).text() for r in sel_rows]

        if len(names) == 1:
            prompt = f"Are you sure you want to delete '{names[0]}'?"
        else:
            prompt = (
                f"Are you sure you want to delete these {len(names)} items?\n"
                + ", ".join(names[:10])
            )

        reply = QMessageBox.question(
            self,
            "Delete Item",
            prompt,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            for item_id in ids:
                delete_item(item_id)
            self.load_inventory()

    def on_delete_all_clicked(self):
        # delete items that are checked in the table
        checked_rows = [
            r
            for r in range(self.table.rowCount())
            if self.table.item(r, 0).checkState() == Qt.CheckState.Checked
        ]
        if not checked_rows:
            QMessageBox.information(
                self,
                "Delete Checked",
                "No items are checked. Use the checkboxes to mark items to delete.",
            )
            return

        items = get_all_items()
        names = [self.table.item(r, 1).text() for r in checked_rows]
        reply = QMessageBox.question(
            self,
            "Delete Checked Items",
            f"Are you sure you want to delete these {len(names)} items?\n"
            + ", ".join(names[:10]),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            ids = [items[r]["id"] for r in checked_rows]
            for item_id in ids:
                delete_item(item_id)
            self.load_inventory()
