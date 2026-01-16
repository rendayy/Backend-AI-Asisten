import os
import sqlite3
from typing import Optional, Dict

DB_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(DB_DIR, "users.db")


def _get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=5)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_db():
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR, exist_ok=True)
    conn = _get_conn()
    try:
        cur = conn.cursor()

        # users
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL
            )
            """
        )

        # revoked JWT
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS revoked_tokens (
                jti TEXT PRIMARY KEY,
                expires_at INTEGER
            )
            """
        )

        # refresh tokens
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS refresh_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token_hash TEXT NOT NULL UNIQUE,
                issued_at INTEGER,
                expires_at INTEGER,
                revoked INTEGER DEFAULT 0,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )

        # TASKS (⬅️ TAMBAHKAN INI)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                due_date INTEGER NOT NULL,
                is_completed INTEGER DEFAULT 0,
                is_notified INTEGER DEFAULT 0,
                created_at INTEGER NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )

        conn.commit()
    finally:
        conn.close()



def find_user(username: str) -> Optional[Dict]:
    _ensure_db()
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, username, email, password_hash, salt FROM users WHERE username = ?", (username,))
        row = cur.fetchone()
        if row is None:
            return None
        return {"id": row["id"], "username": row["username"], "email": row["email"], "password_hash": row["password_hash"], "salt": row["salt"]}
    finally:
        conn.close()


def add_user(username: str, email: str, password_hash: str, salt: str) -> Optional[Dict]:
    _ensure_db()
    conn = _get_conn()
    try:
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO users (username, email, password_hash, salt) VALUES (?, ?, ?, ?)",
                (username, email, password_hash, salt),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            return None
        uid = cur.lastrowid
        return {"id": uid, "username": username, "email": email}
    finally:
        conn.close()


def revoke_token(jti: str, expires_at: int) -> bool:
    """Store a revoked token JTI with its expiry timestamp."""
    _ensure_db()
    conn = _get_conn()
    try:
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO revoked_tokens (jti, expires_at) VALUES (?, ?)", (jti, expires_at))
            conn.commit()
            return True
        except Exception:
            return False
    finally:
        conn.close()


def is_token_revoked(jti: str) -> bool:
    """Return True if the given jti is in revoked_tokens (and not expired)."""
    _ensure_db()
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT expires_at FROM revoked_tokens WHERE jti = ?", (jti,))
        row = cur.fetchone()
        if row is None:
            return False
        expires_at = row["expires_at"]
        # if expired, remove it
        import time

        if expires_at is not None and expires_at < int(time.time()):
            try:
                cur.execute("DELETE FROM revoked_tokens WHERE jti = ?", (jti,))
                conn.commit()
            except Exception:
                pass
            return False
        return True
    finally:
        conn.close()


def store_refresh_token(user_id: int, token_hash: str, issued_at: int, expires_at: int) -> Optional[Dict]:
    _ensure_db()
    conn = _get_conn()
    try:
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO refresh_tokens (user_id, token_hash, issued_at, expires_at, revoked) VALUES (?, ?, ?, ?, 0)",
                (user_id, token_hash, issued_at, expires_at),
            )
            conn.commit()
        except Exception:
            return None
        rid = cur.lastrowid
        return {"id": rid, "user_id": user_id, "token_hash": token_hash, "issued_at": issued_at, "expires_at": expires_at}
    finally:
        conn.close()


def find_refresh_token(token_hash: str) -> Optional[Dict]:
    _ensure_db()
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, user_id, token_hash, issued_at, expires_at, revoked FROM refresh_tokens WHERE token_hash = ?",
            (token_hash,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return {"id": row["id"], "user_id": row["user_id"], "token_hash": row["token_hash"], "issued_at": row["issued_at"], "expires_at": row["expires_at"], "revoked": bool(row["revoked"])}
    finally:
        conn.close()


def revoke_refresh_token(token_hash: str) -> bool:
    _ensure_db()
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE refresh_tokens SET revoked = 1 WHERE token_hash = ?", (token_hash,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def revoke_all_refresh_tokens_for_user(user_id: int) -> int:
    _ensure_db()
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE refresh_tokens SET revoked = 1 WHERE user_id = ?", (user_id,))
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()
