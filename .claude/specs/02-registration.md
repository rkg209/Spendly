## 1. Overview

Implement user registration for Spendly — the `POST /register` route and the `create_user()` DB helper.

A visitor fills in name, email, and password. On success, their account is created and they are redirected to the login page. On failure, the form re-renders with an error message.

---

## 2. Depends on

Step 1 (database setup) — `users` table and `get_db()` must exist.

---

## 3. Routes

### `GET /register`

- Already implemented — renders `register.html`
- No changes needed

### `POST /register`

- Accepts form fields: `name`, `email`, `password`
- Validates inputs:
  - All three fields must be non-empty
  - Password must be at least 8 characters
- On validation failure → re-render `register.html` with `error` context variable
- On duplicate email → re-render `register.html` with `error` context variable
- On success → redirect to `GET /login` using `url_for('login')`

---

## 4. Database

### `create_user(name, email, password)` in `database/db.py`

- Strips whitespace from `name` and `email`
- Lowercases `email` before storing
- Hashes `password` using `werkzeug.security.generate_password_hash`
- Inserts new row into `users` table
- Returns the new user's `id` (integer) on success
- Returns `None` if the email is already taken (UNIQUE constraint violation)
- Must close the DB connection in all cases (use `finally`)

---

## 5. Template changes

### `templates/register.html`

- Form `action` must use `url_for('register')` — not a hardcoded string
- `{{ error }}` block is already present and must display when `error` is in context

---

## 6. Files to Change

- `database/db.py` → add `create_user()`; import `check_password_hash` alongside `generate_password_hash`
- `app.py` → add POST handler to `/register` route; import `request`, `redirect`, `url_for`, `create_user`
- `templates/register.html` → replace hardcoded `action="/register"` with `url_for`

---

## 7. Files to Create

- None

---

## 8. Dependencies

- No new pip packages
- Use:
  - `werkzeug.security.generate_password_hash` (already installed)
  - `sqlite3.IntegrityError` (standard library)

---

## 9. Validation Rules

| Field | Rule | Error message |
|---|---|---|
| name | Non-empty after strip | "All fields are required." |
| email | Non-empty after strip | "All fields are required." |
| password | Non-empty | "All fields are required." |
| password | Length ≥ 8 | "Password must be at least 8 characters." |
| email | Not already in DB | "An account with that email already exists." |

---

## 10. Expected Behavior

- `POST /register` with valid data → user row inserted, redirect to `/login`
- `POST /register` with missing field → 200, re-renders form with error
- `POST /register` with password < 8 chars → 200, re-renders form with error
- `POST /register` with duplicate email → 200, re-renders form with error
- `create_user()` returns integer id on success
- `create_user()` returns `None` on duplicate email
- Emails are stored lowercase
- Passwords are never stored in plaintext

---

## 11. Rules for Implementation

- Use parameterized queries only — no f-strings in SQL
- Never store raw passwords — always hash with `generate_password_hash`
- Use `abort()` for unexpected HTTP errors, not bare string returns
- Use `url_for()` for all redirects and template links
- DB logic belongs in `database/db.py` only — not inline in routes

---

## 12. Definition of Done

- [ ] `create_user()` exists in `database/db.py`
- [ ] `POST /register` is implemented in `app.py`
- [ ] Valid registration inserts a user and redirects to login
- [ ] Duplicate email returns an error without crashing
- [ ] Short password returns an error without crashing
- [ ] Empty fields return an error without crashing
- [ ] `register.html` form action uses `url_for()`
- [ ] Passwords are stored as hashes, never plaintext
