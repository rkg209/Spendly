import pytest
import database.db as db_module
from app import app as flask_app


@pytest.fixture
def app(tmp_path, monkeypatch):
    """
    Provide a Flask app instance configured for testing, backed by a
    fresh in-process SQLite database in a temp directory.  DB_PATH is
    patched so every get_db() call inside routes and helpers uses the
    isolated test DB instead of the real spendly.db.
    """
    test_db_path = str(tmp_path / "test_spendly.db")
    monkeypatch.setattr(db_module, "DB_PATH", test_db_path)

    flask_app.config["TESTING"] = True
    flask_app.config["SECRET_KEY"] = "test-secret-key"

    # Create tables in the fresh test DB (no seed data).
    db_module.init_db()

    yield flask_app


@pytest.fixture
def client(app):
    """Return a Flask test client bound to the isolated test app."""
    return app.test_client()
