import sqlite3

import pytest
from werkzeug.security import check_password_hash

from database.db import get_db, init_db, seed_db

SPEC_CATEGORIES = {"Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"}


# ---------------------------------------------------------------------------
# get_db
# ---------------------------------------------------------------------------

def test_get_db_returns_sqlite_connection():
    conn = get_db()
    assert isinstance(conn, sqlite3.Connection)
    conn.close()


def test_get_db_row_factory_is_sqlite_row():
    conn = get_db()
    conn.execute("CREATE TABLE t (x INTEGER)")
    conn.execute("INSERT INTO t VALUES (42)")
    row = conn.execute("SELECT x FROM t").fetchone()
    assert row["x"] == 42
    conn.close()


def test_get_db_foreign_keys_enabled():
    conn = get_db()
    result = conn.execute("PRAGMA foreign_keys").fetchone()[0]
    assert result == 1
    conn.close()


# ---------------------------------------------------------------------------
# init_db
# ---------------------------------------------------------------------------

def test_init_db_creates_users_table():
    init_db()
    conn = get_db()
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "users" in tables
    conn.close()


def test_init_db_creates_expenses_table():
    init_db()
    conn = get_db()
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "expenses" in tables
    conn.close()


def test_init_db_users_columns():
    init_db()
    conn = get_db()
    cols = {row[1] for row in conn.execute("PRAGMA table_info(users)")}
    assert cols == {"id", "name", "email", "password_hash", "created_at"}
    conn.close()


def test_init_db_expenses_columns():
    init_db()
    conn = get_db()
    cols = {row[1] for row in conn.execute("PRAGMA table_info(expenses)")}
    assert cols == {"id", "user_id", "amount", "category", "date", "description", "created_at"}
    conn.close()


def test_init_db_is_idempotent():
    init_db()
    init_db()  # second call must not raise


# ---------------------------------------------------------------------------
# seed_db
# ---------------------------------------------------------------------------

def test_seed_db_creates_demo_user():
    init_db()
    seed_db()
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email = 'demo@spendly.com'").fetchone()
    assert user is not None
    assert user["name"] == "Demo User"
    conn.close()


def test_seed_db_password_is_hashed():
    init_db()
    seed_db()
    conn = get_db()
    user = conn.execute("SELECT password_hash FROM users").fetchone()
    assert user["password_hash"] != "demo123"
    assert check_password_hash(user["password_hash"], "demo123")
    conn.close()


def test_seed_db_creates_8_expenses():
    init_db()
    seed_db()
    conn = get_db()
    count = conn.execute("SELECT COUNT(*) FROM expenses").fetchone()[0]
    assert count == 8
    conn.close()


def test_seed_db_covers_all_categories():
    init_db()
    seed_db()
    conn = get_db()
    categories = {r[0] for r in conn.execute("SELECT DISTINCT category FROM expenses")}
    assert categories == SPEC_CATEGORIES
    conn.close()


def test_seed_db_expenses_linked_to_demo_user():
    init_db()
    seed_db()
    conn = get_db()
    user_id = conn.execute("SELECT id FROM users").fetchone()[0]
    orphans = conn.execute(
        "SELECT COUNT(*) FROM expenses WHERE user_id != ?", (user_id,)
    ).fetchone()[0]
    assert orphans == 0
    conn.close()


def test_seed_db_amounts_are_float():
    init_db()
    seed_db()
    conn = get_db()
    rows = conn.execute("SELECT amount FROM expenses").fetchall()
    for row in rows:
        assert isinstance(row["amount"], float)
    conn.close()


def test_seed_db_is_idempotent():
    init_db()
    seed_db()
    seed_db()  # second call must not insert duplicates
    conn = get_db()
    assert conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM expenses").fetchone()[0] == 8
    conn.close()


# ---------------------------------------------------------------------------
# Constraints
# ---------------------------------------------------------------------------

def test_fk_enforcement_rejects_invalid_user_id():
    init_db()
    conn = get_db()
    with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"):
        conn.execute(
            "INSERT INTO expenses (user_id, amount, category, date) VALUES (?, ?, ?, ?)",
            (999, 100.0, "Food", "2026-05-05"),
        )
    conn.close()


def test_unique_email_constraint():
    init_db()
    seed_db()
    conn = get_db()
    with pytest.raises(sqlite3.IntegrityError, match="UNIQUE"):
        conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Other", "demo@spendly.com", "hash"),
        )
    conn.close()


def test_users_email_not_null():
    init_db()
    conn = get_db()
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("X", None, "hash"),
        )
    conn.close()


def test_expenses_amount_is_real_not_integer():
    init_db()
    conn = get_db()
    conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("U", "u@test.com", "h"),
    )
    user_id = conn.execute("SELECT id FROM users").fetchone()[0]
    conn.execute(
        "INSERT INTO expenses (user_id, amount, category, date) VALUES (?, ?, ?, ?)",
        (user_id, 99.50, "Food", "2026-05-05"),
    )
    conn.commit()
    row = conn.execute("SELECT amount FROM expenses").fetchone()
    assert row["amount"] == 99.50
    assert isinstance(row["amount"], float)
    conn.close()
