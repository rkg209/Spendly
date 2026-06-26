"""
Tests for Step 02 — User Registration.

Spec: .claude/specs/02-registration.md
Coverage: POST /register happy path, all validation rules, DB side effects,
          create_user() return values, GET /register, and template url_for usage.
"""

import os
import database.db as db_module
from database.db import create_user
from werkzeug.security import check_password_hash


# ---------------------------------------------------------------------------
# GET /register
# ---------------------------------------------------------------------------

def test_get_register_returns_200(client):
    """GET /register must return 200 OK (route already implemented, must not regress)."""
    response = client.get("/register")
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# Template — url_for usage
# ---------------------------------------------------------------------------

def test_register_form_action_uses_url_for():
    """register.html form action must use url_for('register'), not a hardcoded string."""
    template_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "templates", "register.html"
    )
    with open(template_path) as f:
        source = f.read()
    assert "url_for('register')" in source, (
        "register.html must use url_for('register') in the form action, not a hardcoded URL"
    )


# ---------------------------------------------------------------------------
# POST /register — happy path
# ---------------------------------------------------------------------------

def test_valid_registration_redirects_to_login(client):
    """POST /register with valid data must redirect to /login."""
    response = client.post("/register", data={
        "name": "Alice Smith",
        "email": "alice@example.com",
        "password": "securepassword",
    })
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


# ---------------------------------------------------------------------------
# POST /register — validation errors
# ---------------------------------------------------------------------------

def test_missing_name_shows_error(client):
    """POST /register with an empty name must return 200 and render an error."""
    response = client.post("/register", data={
        "name": "",
        "email": "alice@example.com",
        "password": "securepassword",
    })
    assert response.status_code == 200
    assert b"All fields are required." in response.data


def test_missing_email_shows_error(client):
    """POST /register with an empty email must return 200 and render an error."""
    response = client.post("/register", data={
        "name": "Alice Smith",
        "email": "",
        "password": "securepassword",
    })
    assert response.status_code == 200
    assert b"All fields are required." in response.data


def test_missing_password_shows_error(client):
    """POST /register with an empty password must return 200 and render an error."""
    response = client.post("/register", data={
        "name": "Alice Smith",
        "email": "alice@example.com",
        "password": "",
    })
    assert response.status_code == 200
    assert b"All fields are required." in response.data


def test_whitespace_only_name_shows_error(client):
    """POST /register with a whitespace-only name must return 200 and render an error (strip rule)."""
    response = client.post("/register", data={
        "name": "   ",
        "email": "alice@example.com",
        "password": "securepassword",
    })
    assert response.status_code == 200
    assert b"All fields are required." in response.data


def test_short_password_shows_error(client):
    """POST /register with a password shorter than 8 characters must return 200 and render an error."""
    response = client.post("/register", data={
        "name": "Alice Smith",
        "email": "alice@example.com",
        "password": "short",
    })
    assert response.status_code == 200
    assert b"Password must be at least 8 characters." in response.data


def test_password_exactly_7_chars_shows_error(client):
    """POST /register with a 7-character password (one below minimum) must return 200 and an error."""
    response = client.post("/register", data={
        "name": "Alice Smith",
        "email": "alice@example.com",
        "password": "1234567",
    })
    assert response.status_code == 200
    assert b"Password must be at least 8 characters." in response.data


def test_duplicate_email_shows_error(client):
    """POST /register with an already-registered email must return 200 and render an error."""
    # First registration succeeds.
    client.post("/register", data={
        "name": "Alice Smith",
        "email": "alice@example.com",
        "password": "securepassword",
    })
    # Second registration with the same email must fail gracefully.
    response = client.post("/register", data={
        "name": "Alice Duplicate",
        "email": "alice@example.com",
        "password": "anotherpassword",
    })
    assert response.status_code == 200
    assert b"An account with that email already exists." in response.data


def test_duplicate_email_case_insensitive_shows_error(client):
    """POST /register with the same email in different case must return 200 and an error (emails are lowercased)."""
    client.post("/register", data={
        "name": "Alice Smith",
        "email": "alice@example.com",
        "password": "securepassword",
    })
    response = client.post("/register", data={
        "name": "Alice Upper",
        "email": "ALICE@EXAMPLE.COM",
        "password": "anotherpassword",
    })
    assert response.status_code == 200
    assert b"An account with that email already exists." in response.data


# ---------------------------------------------------------------------------
# DB side effects after successful registration
# ---------------------------------------------------------------------------

def test_successful_registration_creates_user_in_db(client):
    """After a valid POST /register, the user row must exist in the users table."""
    client.post("/register", data={
        "name": "Bob Jones",
        "email": "bob@example.com",
        "password": "securepassword",
    })
    conn = db_module.get_db()
    row = conn.execute(
        "SELECT * FROM users WHERE email = ?", ("bob@example.com",)
    ).fetchone()
    conn.close()
    assert row is not None, "User row was not found in the database after registration"


def test_email_stored_lowercase(client):
    """After registration, the stored email must be lowercased regardless of input case."""
    client.post("/register", data={
        "name": "Carol White",
        "email": "Carol.White@Example.COM",
        "password": "securepassword",
    })
    conn = db_module.get_db()
    row = conn.execute(
        "SELECT email FROM users WHERE email = ?", ("carol.white@example.com",)
    ).fetchone()
    conn.close()
    assert row is not None, "Email was not stored in lowercase"
    assert row["email"] == "carol.white@example.com"


def test_password_stored_as_hash_not_plaintext(client):
    """After registration, the stored password_hash must not equal the plaintext password."""
    plaintext = "securepassword"
    client.post("/register", data={
        "name": "Dave Brown",
        "email": "dave@example.com",
        "password": plaintext,
    })
    conn = db_module.get_db()
    row = conn.execute(
        "SELECT password_hash FROM users WHERE email = ?", ("dave@example.com",)
    ).fetchone()
    conn.close()
    assert row is not None
    stored_hash = row["password_hash"]
    assert stored_hash != plaintext, "Password must not be stored as plaintext"
    assert check_password_hash(stored_hash, plaintext), (
        "Stored value must be a valid werkzeug hash of the original password"
    )


# ---------------------------------------------------------------------------
# create_user() unit tests
# ---------------------------------------------------------------------------

def test_create_user_returns_int_id_on_success(app):
    """create_user() must return an integer user id when the email is new."""
    user_id = create_user("Eve Green", "eve@example.com", "securepassword")
    assert isinstance(user_id, int), f"Expected int, got {type(user_id)}"
    assert user_id > 0


def test_create_user_returns_none_on_duplicate_email(app):
    """create_user() must return None when the email is already taken."""
    create_user("Frank Black", "frank@example.com", "securepassword")
    result = create_user("Frank Again", "frank@example.com", "anotherpassword")
    assert result is None, "Expected None for duplicate email, got a user id"


def test_create_user_lowercases_email(app):
    """create_user() must lowercase the email before inserting."""
    create_user("Grace Lee", "Grace.Lee@EXAMPLE.COM", "securepassword")
    conn = db_module.get_db()
    row = conn.execute(
        "SELECT email FROM users WHERE email = ?", ("grace.lee@example.com",)
    ).fetchone()
    conn.close()
    assert row is not None, "Lowercased email not found in DB"


def test_create_user_strips_whitespace_from_name_and_email(app):
    """create_user() must strip leading/trailing whitespace from name and email."""
    create_user("  Henry  ", "  henry@example.com  ", "securepassword")
    conn = db_module.get_db()
    row = conn.execute(
        "SELECT name, email FROM users WHERE email = ?", ("henry@example.com",)
    ).fetchone()
    conn.close()
    assert row is not None, "User not found after stripped email insert"
    assert row["name"] == "Henry"
    assert row["email"] == "henry@example.com"
