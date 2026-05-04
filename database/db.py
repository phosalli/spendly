import sqlite3
from pathlib import Path

from werkzeug.security import generate_password_hash

DB_PATH = Path(__file__).resolve().parent.parent / "expense_tracker.db"


def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT    NOT NULL,
            email         TEXT    NOT NULL UNIQUE,
            password_hash TEXT    NOT NULL,
            created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            amount      REAL    NOT NULL,
            category    TEXT    NOT NULL,
            date        TEXT    NOT NULL,
            description TEXT,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()


def seed_db():
    conn = get_db()
    cur = conn.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] > 0:
        conn.close()
        return

    cur = conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Demo User", "demo@spendly.com", generate_password_hash("demo123")),
    )
    user_id = cur.lastrowid

    expenses = [
        (user_id, 250.00,  "Food",          "2026-05-01", "Lunch at office canteen"),
        (user_id, 150.00,  "Transport",     "2026-05-01", "Auto rickshaw to work"),
        (user_id, 1200.50, "Bills",         "2026-05-02", "Electricity bill — April"),
        (user_id, 450.00,  "Health",        "2026-05-02", "Pharmacy — monthly medicines"),
        (user_id, 350.00,  "Entertainment", "2026-05-03", "Movie ticket — PVR"),
        (user_id, 1899.00, "Shopping",      "2026-05-04", "T-shirt and jeans"),
        (user_id, 99.00,   "Other",         "2026-05-04", "Mobile recharge top-up"),
        (user_id, 480.00,  "Food",          "2026-05-05", "Groceries — weekly"),
    ]
    conn.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        expenses,
    )
    conn.commit()
    conn.close()
