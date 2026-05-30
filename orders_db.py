import sqlite3
from datetime import datetime
from pathlib import Path

from constants import DEFAULT_ORDER_STATUS

DB_PATH = Path(__file__).resolve().parent / "inventory.db"

CREATE_ORDERS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_number TEXT NOT NULL UNIQUE,
    order_name TEXT NOT NULL,
    total_cost REAL NOT NULL DEFAULT 0.0,
    email_id TEXT NOT NULL,
    phone_number TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'New',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""

CREATE_ORDER_ITEMS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    item_name TEXT NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    price_per_unit REAL NOT NULL DEFAULT 0.0,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
)
"""

SAMPLE_ORDERS = [
    ("INV-001", "Order 1", 150.50, "customer1@example.com", "555-0101"),
    ("INV-002", "Order 2", 250.75, "customer2@example.com", "555-0102"),
    ("INV-003", "Order 3", 100.00, "customer3@example.com", "555-0103"),
]


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_orders_db():
    with get_connection() as conn:
        conn.execute(CREATE_ORDERS_TABLE_SQL)
        conn.execute(CREATE_ORDER_ITEMS_TABLE_SQL)

        # Ensure old databases gain the new status and timestamp columns.
        columns = [row[1] for row in conn.execute("PRAGMA table_info('orders')").fetchall()]
        if "status" not in columns:
            default_status = DEFAULT_ORDER_STATUS.replace("'", "''")
            conn.execute(f"ALTER TABLE orders ADD COLUMN status TEXT NOT NULL DEFAULT '{default_status}'")

        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        if "created_at" not in columns:
            conn.execute(
                f"ALTER TABLE orders ADD COLUMN created_at TEXT NOT NULL DEFAULT '{now}'"
            )
            conn.execute("UPDATE orders SET created_at = ?", (now,))
        if "updated_at" not in columns:
            conn.execute(
                f"ALTER TABLE orders ADD COLUMN updated_at TEXT NOT NULL DEFAULT '{now}'"
            )
            conn.execute("UPDATE orders SET updated_at = ?", (now,))

        cursor = conn.execute("SELECT COUNT(1) FROM orders")
        count = cursor.fetchone()[0]
        if count == 0:
            conn.executemany(
                "INSERT INTO orders (invoice_number, order_name, total_cost, email_id, phone_number) VALUES (?, ?, ?, ?, ?)",
                SAMPLE_ORDERS,
            )
            conn.commit()


def generate_invoice_number() -> str:
    """Generate a unique invoice number based on the highest existing ID."""
    with get_connection() as conn:
        cursor = conn.execute("SELECT MAX(id) FROM orders")
        result = cursor.fetchone()
        max_id = result[0] if result[0] is not None else 0
        return f"INV-{max_id + 1:03d}"


def get_all_orders():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, invoice_number, order_name, total_cost, email_id, phone_number, status, created_at, updated_at FROM orders ORDER BY invoice_number"
        ).fetchall()
    return rows


def get_order_invoice_number(invoice_number: str):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, invoice_number, order_name, total_cost, email_id, phone_number, status, created_at, updated_at FROM orders WHERE invoice_number = ? COLLATE NOCASE",
            (invoice_number,),
        ).fetchone()
    return row


def order_exists(invoice_number: str, exclude_id: int = None) -> bool:
    with get_connection() as conn:
        if exclude_id is None:
            cursor = conn.execute(
                "SELECT 1 FROM orders WHERE invoice_number = ? COLLATE NOCASE LIMIT 1",
                (invoice_number,),
            )
        else:
            cursor = conn.execute(
                "SELECT 1 FROM orders WHERE invoice_number = ? COLLATE NOCASE AND id != ? LIMIT 1",
                (invoice_number, exclude_id),
            )
        return cursor.fetchone() is not None


def add_order(
    order_name: str,
    total_cost: float,
    email_id: str,
    phone_number: str,
    status: str = DEFAULT_ORDER_STATUS,
    items: list = None,
):
    """Add a new order with auto-generated invoice number.

    Args:
        order_name: Name of the order
        total_cost: Total cost of the order
        email_id: Customer email
        phone_number: Customer phone
        status: Order status
        items: List of tuples (item_name, quantity, price_per_unit)
    """
    invoice_number = generate_invoice_number()
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO orders (invoice_number, order_name, total_cost, email_id, phone_number, status) VALUES (?, ?, ?, ?, ?, ?)",
            (invoice_number, order_name, total_cost, email_id, phone_number, status),
        )
        order_id = cursor.lastrowid
        if items:
            for item_name, quantity, price_per_unit in items:
                conn.execute(
                    "INSERT INTO order_items (order_id, item_name, quantity, price_per_unit) VALUES (?, ?, ?, ?)",
                    (order_id, item_name, quantity, price_per_unit),
                )
        conn.commit()
    return invoice_number


def update_order(
    order_id: int,
    invoice_number: str,
    order_name: str,
    total_cost: float,
    email_id: str,
    phone_number: str,
    status: str,
    items: list = None,
):
    with get_connection() as conn:
        conn.execute(
            "UPDATE orders SET invoice_number = ?, order_name = ?, total_cost = ?, email_id = ?, phone_number = ?, status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (invoice_number, order_name, total_cost, email_id, phone_number, status, order_id),
        )
        if items is not None:
            conn.execute("DELETE FROM order_items WHERE order_id = ?", (order_id,))
            for item_name, quantity, price_per_unit in items:
                conn.execute(
                    "INSERT INTO order_items (order_id, item_name, quantity, price_per_unit) VALUES (?, ?, ?, ?)",
                    (order_id, item_name, quantity, price_per_unit),
                )
        conn.commit()


def get_order_items(order_id: int):
    """Get all items for a specific order."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, item_name, quantity, price_per_unit FROM order_items WHERE order_id = ? ORDER BY item_name",
            (order_id,),
        ).fetchall()
    return rows


def delete_order(order_id: int):
    """Delete an order by id (order_items cascade deleted)."""
    with get_connection() as conn:
        conn.execute("DELETE FROM orders WHERE id = ?", (order_id,))
        conn.commit()
