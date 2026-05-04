import pytest
import database.db


@pytest.fixture(autouse=True)
def temp_db(monkeypatch, tmp_path):
    """Redirect every test to an isolated temp database."""
    monkeypatch.setattr(database.db, "DB_PATH", tmp_path / "test.db")
