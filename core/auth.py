
"""Authentication and password-reset helpers for CareerCompass AI."""

import hashlib
import hmac
import os
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
AUTH_DB_PATH = Path(
    os.getenv("CAREERCOMPASS_AUTH_DB", str(BASE_DIR / "auth.db"))
)


def _now():
    return datetime.now(timezone.utc)


def _connect():
    AUTH_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(AUTH_DB_PATH), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 10000")

    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE COLLATE NOCASE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            token_hash TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            used INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """
    )
    conn.commit()
    return conn


def _hash_password(password, salt=None):
    """Hash a password using PBKDF2-HMAC-SHA256."""
    salt = salt or secrets.token_bytes(16)
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        600_000,
    )
    return f"{salt.hex()}${derived.hex()}"


def _verify_password(password, stored_hash):
    try:
        salt_hex, expected_hex = stored_hash.split("$", 1)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(expected_hex)
    except (ValueError, TypeError):
        return False

    actual = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        600_000,
    )
    return hmac.compare_digest(actual, expected)


def register_user(name, email, password):
    """Register a user. Returns (success, message, user_id)."""
    name = (name or "").strip()
    email = (email or "").strip().lower()

    if not name:
        return False, "Please enter your name.", None

    if len(name) > 100:
        return False, "Name must be 100 characters or fewer.", None

    if not email or "@" not in email or len(email) > 254:
        return False, "Please enter a valid email address.", None

    if len(password or "") < 8:
        return False, "Password must contain at least 8 characters.", None

    if len(password) > 1024:
        return False, "Password is too long.", None

    user_id = secrets.token_hex(16)
    password_hash = _hash_password(password)

    conn = _connect()
    try:
        conn.execute(
            """
            INSERT INTO users (id, name, email, password_hash, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                name,
                email,
                password_hash,
                _now().isoformat(),
            ),
        )
        conn.commit()
        return True, "Account created successfully.", user_id
    except sqlite3.IntegrityError:
        return False, "An account with this email already exists.", None
    finally:
        conn.close()


def authenticate_user(email, password):
    """Verify login credentials. Returns the user or None."""
    email = (email or "").strip().lower()

    conn = _connect()
    try:
        user = conn.execute(
            """
            SELECT id, name, email, password_hash
            FROM users
            WHERE email = ?
            """,
            (email,),
        ).fetchone()

        if user and _verify_password(password or "", user["password_hash"]):
            return {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
            }

        return None
    finally:
        conn.close()


def create_reset_token(email):
    """Create a one-time, 30-minute password-reset token."""
    email = (email or "").strip().lower()
    raw_token = secrets.token_urlsafe(32)

    conn = _connect()
    try:
        user = conn.execute(
            "SELECT id FROM users WHERE email = ?",
            (email,),
        ).fetchone()

        if not user:
            return None

        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        expires_at = (_now() + timedelta(minutes=30)).isoformat()

        conn.execute(
            """
            UPDATE password_reset_tokens
            SET used = 1
            WHERE user_id = ? AND used = 0
            """,
            (user["id"],),
        )

        conn.execute(
            """
            INSERT INTO password_reset_tokens
                (token_hash, user_id, expires_at, used)
            VALUES (?, ?, ?, 0)
            """,
            (token_hash, user["id"], expires_at),
        )
        conn.commit()
        return raw_token
    finally:
        conn.close()


def reset_password(token, new_password):
    """Consume a valid reset token and update the user's password."""
    if not token:
        return False, "The reset link is invalid or expired."

    if len(new_password or "") < 8:
        return False, "Password must contain at least 8 characters."

    if len(new_password) > 1024:
        return False, "Password is too long."

    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()

    conn = _connect()
    try:
        conn.execute("BEGIN IMMEDIATE")

        record = conn.execute(
            """
            SELECT token_hash, user_id, expires_at
            FROM password_reset_tokens
            WHERE token_hash = ? AND used = 0
            """,
            (token_hash,),
        ).fetchone()

        if not record:
            conn.rollback()
            return False, "The reset link is invalid or has already been used."

        expiry = datetime.fromisoformat(record["expires_at"])
        if expiry <= _now():
            conn.execute(
                "UPDATE password_reset_tokens SET used = 1 WHERE token_hash = ?",
                (token_hash,),
            )
            conn.commit()
            return False, "The reset link has expired. Request a new one."

        conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (_hash_password(new_password), record["user_id"]),
        )
        conn.execute(
            "UPDATE password_reset_tokens SET used = 1 WHERE token_hash = ?",
            (token_hash,),
        )
        conn.commit()
        return True, "Password updated successfully. You can now log in."
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
