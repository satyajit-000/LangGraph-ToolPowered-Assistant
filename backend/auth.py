import sqlite3, hashlib, secrets, datetime
from .db import conn


# ----------------
# Helpers
# ----------------
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash


# ----------------
# Auth: Sign Up
# ----------------
def sign_up(email: str, password: str, first_name: str, last_name: str | None) -> int:
    password_hash = hash_password(password)

    try:
        cur = conn.cursor()
        cur.execute(
        "SELECT id, password_hash FROM users WHERE email = ?",
            (email,),
        )
        row = cur.fetchone()

        if row:
            raise ValueError("Account already exists")
        cur.execute(
            "INSERT INTO users (first_name, last_name, email, password_hash) VALUES (?, ?, ?, ?)",
            (first_name, last_name, email, password_hash),
        )
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError:
        raise ValueError("Email already registered")


# ----------------
# Auth: Sign In
# ----------------
def sign_in(email: str, password: str) -> int:
    cur = conn.cursor()
    cur.execute(
        "SELECT id, password_hash FROM users WHERE email = ?",
        (email,),
    )
    row = cur.fetchone()

    if not row:
        raise ValueError("Account doesn't exists")

    user_id, password_hash = row

    if not verify_password(password, password_hash):
        raise ValueError("Invalid email or password")

    return user_id


# ----------------
# Password Reset
# ----------------
def create_reset_token(email: str) -> str:
    now = datetime.datetime.now(datetime.timezone.utc)

    cur = conn.cursor()
    cur.execute(
        """
        SELECT token, expires_at
        FROM password_resets
        WHERE email = ?
        """,
        (email,),
    )
    row = cur.fetchone()
    print(row)
    if not row:
        raise ValueError("Account doesn't exists")
    token, expires_at = row
    expires_at = datetime.datetime.fromisoformat(expires_at)

    # Make stored value UTC-aware if needed
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=datetime.timezone.utc)

    if now <= expires_at:
        return token

    conn.execute(
        "DELETE FROM password_resets WHERE email = ?",
        (email,),
    )
    conn.commit()

    token = secrets.token_urlsafe(32)
    expires_at = now + datetime.timedelta(minutes=30)

    conn.execute(
        """
        INSERT INTO password_resets (email, token, expires_at)
        VALUES (?, ?, ?)
        """,
        (email, token, expires_at.isoformat()),
    )
    conn.commit()

    return token



def reset_password(token: str, new_password: str):
    cur = conn.cursor()
    cur.execute(
        """
        SELECT email, expires_at FROM password_resets
        WHERE token = ?
        """,
        (token,),
    )
    row = cur.fetchone()

    if not row:
        raise ValueError("Invalid or expired reset token")

    email, expires_at = row

    expires = datetime.datetime.fromisoformat(expires_at).replace(
        tzinfo=datetime.timezone.utc
    )

    if datetime.datetime.now(datetime.timezone.utc) > expires:
         # 🔥 flush expired token
        conn.execute(
            "DELETE FROM password_resets WHERE token = ?",
            (token,),
        )
        conn.commit()
        raise ValueError("Reset token expired")

    new_hash = hash_password(new_password)

    conn.execute(
        "UPDATE users SET password_hash = ? WHERE email = ?",
        (new_hash, email),
    )
    conn.execute(
        "DELETE FROM password_resets WHERE token = ?",
        (token,),
    )
    conn.commit()


def flush_expired_tokens():
    conn.execute(
        "DELETE FROM password_resets WHERE expires_at < ?",
        (datetime.datetime.now(datetime.timezone.utc).isoformat(),),
    )
    conn.commit()
