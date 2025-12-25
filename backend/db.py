import sqlite3, datetime
from typing import Optional

conn = sqlite3.connect("chatbot.db", check_same_thread=False)

def init_db():
    conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name VARCHAR(20) NOT NULL,
        last_name VARCHAR(20) DEFAULT NULL,
        email TEXT UNIQUE,
        password_hash TEXT
    );
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS chat_rooms (
        thread_id TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        thread_title TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS password_resets (
        email TEXT PRIMARY KEY,
        token TEXT,
        expires_at TEXT
    );
    """)

    conn.execute(
        "DELETE FROM password_resets WHERE expires_at < ?",
        (datetime.datetime.now(datetime.timezone.utc).isoformat(),),
    )

    conn.commit()


# ---------- Chat room helpers ----------

def get_thread_title(thread_id: str, user_id: int) -> Optional[str]:
    cur = conn.cursor()
    cur.execute(
        "SELECT thread_title FROM chat_rooms WHERE thread_id=? AND user_id=?",
        (thread_id, user_id)
    )
    row = cur.fetchone()
    return row[0] if row else None


def set_thread_title(thread_id: str, user_id: int, title: str):
    conn.execute(
        """
        INSERT OR IGNORE INTO chat_rooms (thread_id, user_id, thread_title)
        VALUES (?, ?, ?)
        """,
        (thread_id, user_id, title)
    )
    conn.execute(
        """
        UPDATE chat_rooms
        SET thread_title=?
        WHERE thread_id=? AND user_id=?
        """,
        (title, thread_id, user_id)
    )
    conn.commit()


def get_user_rooms(user_id: int):
    cur = conn.cursor()
    cur.execute(
        "SELECT thread_id, thread_title FROM chat_rooms WHERE user_id=? ORDER BY created_at DESC",
        (user_id,)
    )
    return cur.fetchall()

def get_user_details(user_id: int):
    cur = conn.cursor()
    cur.execute(
        'SELECT first_name, last_name, email FROM users WHERE id=?',
        (user_id,)
    )
    row = cur.fetchone()

    if row is None:
        return None
    
    first_name, last_name, email = row
    
    return {
        'first_name': first_name,
        'last_name': last_name,
        'email': email,
    }


def get_connection():
    return conn
