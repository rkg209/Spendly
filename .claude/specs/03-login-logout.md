# Spec: Login and Logout

## Overview
Implement session-based authentication for Spendly. A registered user submits their email and password via `POST /login`; on success, their `user_id` and `name` are stored in a Flask session and they are redirected to `/profile`. `GET /logout` clears the session and redirects to the landing page. The nav bar updates to reflect login state. This step unlocks all subsequent authenticated routes.

## Depends on
- Step 01 (database setup) — `users` table, `get_db()`, `init_db()`, `seed_db()` must exist.
- Step 02 (registration) — `create_user()` must exist; a user must be registerable before login is testable.

## Routes

- `GET /login` — already implemented; no change to GET logic, but route must now accept POST
- `POST /login` — validates credentials, sets session, redirects to `/profile` — public
- `GET /logout` — clears session, redirects to `/` — public (no auth guard needed, safe to call even if not logged in)

## Database changes

### New function: `get_user_by_email(email)` in `database/db.py`
- Strips and lowercases `email` before querying
- Returns the matching `sqlite3.Row` from `users`, or `None` if not found
- Closes the connection in all cases (use `finally`)

No new tables or columns needed.

## Templates

- **Modify:** `templates/login.html`
  - Replace hardcoded `action="/login"` with `action="{{ url_for('login') }}"`
- **Modify:** `templates/base.html`
  - Nav links must be conditional on `session.get('user_id')`:
    - **Logged in:** show "Hi, {name}" (non-linked) and a "Sign out" link pointing to `url_for('logout')`
    - **Logged out:** show existing "Sign in" and "Get started" links

## Files to change

- `database/db.py` — add `get_user_by_email()`
- `app.py` — set `app.secret_key`, add `session` to imports, add `POST /login` handler, implement `GET /logout`, import `get_user_by_email` and `check_password_hash`
- `templates/login.html` — fix hardcoded form action
- `templates/base.html` — conditional nav links

## Files to create

None.

## New dependencies

No new pip packages. Uses:
- `flask.session` (built into Flask)
- `werkzeug.security.check_password_hash` (already installed)

## Rules for implementation

- No SQLAlchemy or ORMs
- Parameterised queries only — never f-strings in SQL
- Passwords verified with `werkzeug.security.check_password_hash` — never compare plaintext
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- `app.secret_key` must be set before any session usage; use a hardcoded dev string (e.g. `"spendly-dev-secret"`) — acceptable for this learning project
- Session keys: store `session['user_id']` (integer) and `session['user_name']` (string) on login
- `GET /logout` must call `session.clear()` then redirect — use `url_for('landing')`
- DB logic stays in `database/db.py` — no inline queries in routes
- Use `abort()` for unexpected HTTP errors, not bare string returns

## Definition of done

- [ ] `get_user_by_email()` exists in `database/db.py` and returns a `sqlite3.Row` or `None`
- [ ] `POST /login` with valid credentials sets `session['user_id']` and `session['user_name']`, then redirects to `/profile`
- [ ] `POST /login` with wrong password re-renders `login.html` with `error="Invalid email or password."`
- [ ] `POST /login` with unknown email re-renders `login.html` with `error="Invalid email or password."` (no user-enumeration leak)
- [ ] `POST /login` with empty fields re-renders `login.html` with `error="All fields are required."`
- [ ] `GET /logout` clears the session and redirects to the landing page
- [ ] Nav bar shows "Sign out" link when logged in and "Sign in" / "Get started" when logged out
- [ ] `login.html` form action uses `url_for('login')` — no hardcoded URL
- [ ] Demo user (`demo@spendly.com` / `demo123`) can log in successfully
