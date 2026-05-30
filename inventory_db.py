import sqlite3
from pathlib import Path

from constants import FILAMENTS

DB_PATH = Path(__file__).resolve().parent / "inventory.db"
DEFAULT_MATERIAL = FILAMENTS[0] if FILAMENTS else "PLA"

CREATE_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS inventory_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_name TEXT NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 0,
    price REAL NOT NULL DEFAULT 0.0,
    status TEXT NOT NULL DEFAULT 'In Stock',
    material TEXT NOT NULL DEFAULT '{DEFAULT_MATERIAL}'
)
"""

SAMPLE_ITEMS = [
    ("PLA Filament", 25, 500.0, "In Stock", DEFAULT_MATERIAL),
    ("Resin", 12, 50.0, "In Stock", DEFAULT_MATERIAL),
    ("Build Plate", 3, 10.0, "Low", DEFAULT_MATERIAL),
]


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_db():
    with get_connection() as conn:
        conn.execute(CREATE_TABLE_SQL)
        existing_columns = [
            row[1]
            for row in conn.execute("PRAGMA table_info(inventory_items)").fetchall()
        ]
        if "material" not in existing_columns:
            conn.execute(
                f"ALTER TABLE inventory_items ADD COLUMN material TEXT NOT NULL DEFAULT '{DEFAULT_MATERIAL}'"
            )
        cursor = conn.execute("SELECT COUNT(1) FROM inventory_items")
        count = cursor.fetchone()[0]
        if count == 0:
            conn.executemany(
                "INSERT INTO inventory_items (item_name, quantity, price, status, material) VALUES (?, ?, ?, ?, ?)",
                SAMPLE_ITEMS,
            )
            conn.commit()


def get_all_items():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, item_name, quantity, price, status, material FROM inventory_items ORDER BY item_name"
        ).fetchall()
    return rows


def item_exists(item_name: str, exclude_id: int = None) -> bool:
    with get_connection() as conn:
        if exclude_id is None:
            cursor = conn.execute(
                "SELECT 1 FROM inventory_items WHERE item_name = ? COLLATE NOCASE LIMIT 1",
                (item_name,),
            )
        else:
            cursor = conn.execute(
                "SELECT 1 FROM inventory_items WHERE item_name = ? COLLATE NOCASE AND id != ? LIMIT 1",
                (item_name, exclude_id),
            )
        return cursor.fetchone() is not None


def add_item(item_name: str, quantity: int, price: float, status: str, material: str):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO inventory_items (item_name, quantity, price, status, material) VALUES (?, ?, ?, ?, ?)",
            (item_name, quantity, price, status, material),
        )
        conn.commit()


def update_item(item_id: int, item_name: str, quantity: int, price: float, status: str, material: str):
    with get_connection() as conn:
        conn.execute(
            "UPDATE inventory_items SET item_name = ?, quantity = ?, price = ?, status = ?, material = ? WHERE id = ?",
            (item_name, quantity, price, status, material, item_id),
        )
        conn.commit()


def delete_item(item_id: int):
    """Delete an inventory item by id."""
    with get_connection() as conn:
        conn.execute("DELETE FROM inventory_items WHERE id = ?", (item_id,))
        conn.commit()
