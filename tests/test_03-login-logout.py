"""
Tests for Step 03 — Login and Logout.

Spec: .claude/specs/03-login-logout.md
Coverage: POST /login happy path, validation errors, credential failures,
          session contents after login/logout, GET /logout, nav state
          (logged-in vs logged-out), template url_for usage, and
          password-with-spaces acceptance.
"""

import os
import database.db as db_module
from database.db import create_user


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _login(client, email="alice@example.com", password="securepass"):
    """POST to /login and return the response."""
    return client.post("/login", data={"email": email, "password": password})


# ---------------------------------------------------------------------------
# GET /login
# ---------------------------------------------------------------------------

def test_get_login_returns_200(client):
    """GET /login must return 200 OK."""
    response = client.get("/login")
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# Template checks
# ---------------------------------------------------------------------------

def test_login_form_action_uses_url_for():
    """login.html form action must use url_for('login'), not a hardcoded URL."""
    template_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "templates", "login.html"
    )
    with open(template_path) as f:
        source = f.read()
    assert "url_for('login')" in source, (
        "login.html must use url_for('login') in the form action"
    )
    assert 'action="/login"' not in source, (
        "login.html must not hardcode action=\"/login\""
    )


def test_base_nav_has_conditional_session_block():
    """base.html nav must be conditional on session.get('user_id') and include a sign-out link."""
    template_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "templates", "base.html"
    )
    with open(template_path) as f:
        source = f.read()
    assert "session.get('user_id')" in source, (
        "base.html must check session.get('user_id') to conditionally render nav links"
    )
    assert "url_for('logout')" in source, (
        "base.html must include a Sign out link using url_for('logout')"
    )


# ---------------------------------------------------------------------------
# POST /login — happy path
# ---------------------------------------------------------------------------

def test_valid_login_redirects_to_profile(client):
    """POST /login with valid credentials must redirect to /profile."""
    create_user("Alice Smith", "alice@example.com", "securepass")
    response = _login(client)
    assert response.status_code == 302
    assert "/profile" in response.headers["Location"]


def test_valid_login_sets_user_id_in_session(client):
    """After a valid login, session['user_id'] must be set to an integer."""
    create_user("Alice Smith", "alice@example.com", "securepass")
    _login(client)
    with client.session_transaction() as sess:
        assert "user_id" in sess, "session['user_id'] was not set after login"
        assert isinstance(sess["user_id"], int), (
            f"session['user_id'] must be int, got {type(sess['user_id'])}"
        )


def test_valid_login_sets_user_name_in_session(client):
    """After a valid login, session['user_name'] must be set to the user's name as a string."""
    create_user("Alice Smith", "alice@example.com", "securepass")
    _login(client)
    with client.session_transaction() as sess:
        assert "user_name" in sess, "session['user_name'] was not set after login"
        assert isinstance(sess["user_name"], str), (
            f"session['user_name'] must be str, got {type(sess['user_name'])}"
        )
        assert sess["user_name"] == "Alice Smith"


def test_valid_login_session_user_id_matches_db(client):
    """After login, session['user_id'] must equal the id returned by create_user()."""
    user_id = create_user("Bob Jones", "bob@example.com", "securepass123")
    _login(client, email="bob@example.com", password="securepass123")
    with client.session_transaction() as sess:
        assert sess["user_id"] == user_id


def test_demo_credentials_can_login(client):
    """A user created with demo-style credentials must be able to log in successfully."""
    # conftest does NOT call seed_db(), so we create the demo user explicitly.
    create_user("Demo User", "demo@spendly.com", "demo123")
    response = client.post("/login", data={
        "email": "demo@spendly.com",
        "password": "demo123",
    })
    assert response.status_code == 302
    assert "/profile" in response.headers["Location"]


# ---------------------------------------------------------------------------
# POST /login — validation errors (empty fields)
# ---------------------------------------------------------------------------

def test_login_empty_email_shows_required_error(client):
    """POST /login with empty email must re-render login.html with 'All fields are required.'"""
    response = client.post("/login", data={"email": "", "password": "securepass"})
    assert response.status_code == 200
    assert b"All fields are required." in response.data


def test_login_empty_password_shows_required_error(client):
    """POST /login with empty password must re-render login.html with 'All fields are required.'"""
    response = client.post("/login", data={"email": "alice@example.com", "password": ""})
    assert response.status_code == 200
    assert b"All fields are required." in response.data


def test_login_both_fields_empty_shows_required_error(client):
    """POST /login with both fields empty must show 'All fields are required.'"""
    response = client.post("/login", data={"email": "", "password": ""})
    assert response.status_code == 200
    assert b"All fields are required." in response.data


def test_login_whitespace_only_email_shows_required_error(client):
    """POST /login with whitespace-only email (stripped to empty) must show 'All fields are required.'"""
    response = client.post("/login", data={"email": "   ", "password": "securepass"})
    assert response.status_code == 200
    assert b"All fields are required." in response.data


# ---------------------------------------------------------------------------
# POST /login — credential failures (no user enumeration)
# ---------------------------------------------------------------------------

def test_login_unknown_email_shows_invalid_credentials_error(client):
    """POST /login with an unregistered email must return 'Invalid email or password.'"""
    response = client.post("/login", data={
        "email": "nobody@example.com",
        "password": "anypassword",
    })
    assert response.status_code == 200
    assert b"Invalid email or password." in response.data


def test_login_wrong_password_shows_invalid_credentials_error(client):
    """POST /login with a known email but wrong password must return 'Invalid email or password.'"""
    create_user("Alice Smith", "alice@example.com", "correctpass")
    response = client.post("/login", data={
        "email": "alice@example.com",
        "password": "wrongpassword",
    })
    assert response.status_code == 200
    assert b"Invalid email or password." in response.data


def test_unknown_email_and_wrong_password_produce_identical_error(client):
    """Unknown email and wrong password must produce the exact same error message — no user enumeration leak."""
    create_user("Alice Smith", "alice@example.com", "correctpass")

    unknown_email_resp = client.post("/login", data={
        "email": "nobody@example.com",
        "password": "anypassword",
    })
    wrong_password_resp = client.post("/login", data={
        "email": "alice@example.com",
        "password": "wrongpassword",
    })

    assert b"Invalid email or password." in unknown_email_resp.data, (
        "Unknown email must show 'Invalid email or password.'"
    )
    assert b"Invalid email or password." in wrong_password_resp.data, (
        "Wrong password must show 'Invalid email or password.'"
    )
    # Neither should leak a different message that reveals whether the email exists
    assert b"All fields are required." not in unknown_email_resp.data
    assert b"All fields are required." not in wrong_password_resp.data


# ---------------------------------------------------------------------------
# POST /login — password with spaces is valid (not stripped)
# ---------------------------------------------------------------------------

def test_login_password_with_spaces_is_valid(client):
    """A password containing spaces must be accepted — the route must not strip the password field."""
    spaced_password = "pass word 123"
    create_user("Alice Smith", "alice@example.com", spaced_password)
    response = client.post("/login", data={
        "email": "alice@example.com",
        "password": spaced_password,
    })
    assert response.status_code == 302, (
        "Login with a password containing spaces should succeed (passwords are not stripped)"
    )
    assert "/profile" in response.headers["Location"]


# ---------------------------------------------------------------------------
# GET /logout
# ---------------------------------------------------------------------------

def test_logout_redirects_to_landing(client):
    """GET /logout must redirect to the landing page (/)."""
    create_user("Alice Smith", "alice@example.com", "securepass")
    _login(client)
    response = client.get("/logout")
    assert response.status_code == 302
    location = response.headers["Location"]
    assert location in ("/", "http://localhost/"), (
        f"Expected redirect to '/', got '{location}'"
    )


def test_logout_clears_user_id_from_session(client):
    """After logout, session['user_id'] must not be present."""
    create_user("Alice Smith", "alice@example.com", "securepass")
    _login(client)
    client.get("/logout")
    with client.session_transaction() as sess:
        assert "user_id" not in sess, "session['user_id'] was not cleared after logout"


def test_logout_clears_user_name_from_session(client):
    """After logout, session['user_name'] must not be present."""
    create_user("Alice Smith", "alice@example.com", "securepass")
    _login(client)
    client.get("/logout")
    with client.session_transaction() as sess:
        assert "user_name" not in sess, "session['user_name'] was not cleared after logout"


def test_logout_session_is_completely_empty(client):
    """After logout, the session must be fully empty — session.clear() must have been called."""
    create_user("Alice Smith", "alice@example.com", "securepass")
    _login(client)
    client.get("/logout")
    with client.session_transaction() as sess:
        assert len(sess) == 0, (
            f"Session was not fully cleared; remaining keys: {list(sess.keys())}"
        )


def test_logout_without_active_session_is_safe(client):
    """GET /logout with no active session must not raise an error — it must redirect safely."""
    response = client.get("/logout")
    assert response.status_code == 302, (
        "Logout without a session must still return a redirect, not a 500 error"
    )


# ---------------------------------------------------------------------------
# Nav state — logged out
# ---------------------------------------------------------------------------

def test_nav_shows_sign_in_when_logged_out(client):
    """Without a session, the nav must show a 'Sign in' link."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Sign in" in response.data


def test_nav_shows_get_started_when_logged_out(client):
    """Without a session, the nav must show a 'Get started' link."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Get started" in response.data


# ---------------------------------------------------------------------------
# Nav state — logged in
# ---------------------------------------------------------------------------

def test_nav_shows_hi_name_after_login(client):
    """After login, the nav must display 'Hi, {name}' using the logged-in user's name."""
    create_user("Alice Smith", "alice@example.com", "securepass")
    _login(client)
    response = client.get("/")
    assert response.status_code == 200
    assert b"Hi, Alice Smith" in response.data


def test_nav_shows_sign_out_link_after_login(client):
    """After login, the nav must contain a 'Sign out' link."""
    create_user("Alice Smith", "alice@example.com", "securepass")
    _login(client)
    response = client.get("/")
    assert response.status_code == 200
    assert b"Sign out" in response.data


def test_nav_hides_get_started_after_login(client):
    """After login, the 'Get started' link must not appear in the nav."""
    create_user("Alice Smith", "alice@example.com", "securepass")
    _login(client)
    response = client.get("/")
    assert response.status_code == 200
    assert b"Get started" not in response.data


# ---------------------------------------------------------------------------
# Nav state — after logout (reverts to logged-out links)
# ---------------------------------------------------------------------------

def test_nav_shows_sign_in_after_logout(client):
    """After logout, the nav must revert to showing the 'Sign in' link."""
    create_user("Alice Smith", "alice@example.com", "securepass")
    _login(client)
    client.get("/logout")
    response = client.get("/")
    assert response.status_code == 200
    assert b"Sign in" in response.data


def test_nav_hides_sign_out_after_logout(client):
    """After logout, the 'Sign out' link must not appear in the nav."""
    create_user("Alice Smith", "alice@example.com", "securepass")
    _login(client)
    client.get("/logout")
    response = client.get("/")
    assert response.status_code == 200
    assert b"Sign out" not in response.data
