import sqlite3, datetime
from typing import Literal, Optional, List, Dict, Any

conn = sqlite3.connect("chatbot.db", check_same_thread=False)

def init_db():
    conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name VARCHAR(20) NOT NULL,
        last_name VARCHAR(20) DEFAULT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1)),
        is_admin INTEGER NOT NULL DEFAULT 0 CHECK (is_admin IN (0,1))     
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

    conn.row_factory = sqlite3.Row
    conn.commit()


# ---------- Chat room helpers ----------


def execute_select_query(
    select_query: str,
    parameters: tuple = (),
    fetch: Literal["one", "all", "many"] = "all",
    many_size: int = 10
) -> Optional[Dict[str, Any] | List[Dict[str, Any]]]:

    curr = conn.execute(select_query, parameters)

    try:
        match(fetch):
            case "one":
                row = curr.fetchone()
                return dict(row) if row else None

            case "many":
                rows = curr.fetchmany(many_size)
                return [dict(row) for row in rows]

            case "all":  # fetch == "all"
                rows = curr.fetchall()
                return [dict(row) for row in rows]
            
            case _:
                raise ValueError(f"Invalid fetch mode: {fetch}")


    finally:
        curr.close()


def get_thread_title(thread_id: str, user_id: int) -> Optional[str]:
    row = execute_select_query(
        "SELECT thread_title FROM chat_rooms WHERE thread_id=? AND user_id=?",
        (thread_id, user_id),
        fetch="one"
    )
    return row["thread_title"] if row else None


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
    return execute_select_query(
        """
        SELECT thread_id, thread_title
        FROM chat_rooms
        WHERE user_id=?
        ORDER BY created_at DESC
        """,
        (user_id,),
        fetch="all"
    )

def get_user_details(user_id: int):
    return execute_select_query(
        "SELECT first_name, last_name, email, is_active, is_admin FROM users WHERE id=?",
        (user_id,),
        fetch="one"
    )


def get_connection():
    return conn
