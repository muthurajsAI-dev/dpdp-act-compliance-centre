import sqlite3
import os
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), 'app_data.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def create_user(email, password_hash):
    conn = get_db()
    try:
        conn.execute(
            'INSERT INTO users (email, password_hash, created_at) VALUES (?, ?, ?)',
            (email, password_hash, datetime.now(timezone.utc).isoformat())
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # email already exists
    finally:
        conn.close()

def get_user_by_email(email):
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()
    return user

def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            title TEXT NOT NULL DEFAULT 'New conversation',
            created_at TEXT NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (conversation_id) REFERENCES conversations (id)
        )
    ''')
    conn.commit()
    conn.close()

def create_conversation(user_email, title="New conversation"):
    conn = get_db()
    cursor = conn.execute(
        'INSERT INTO conversations (user_email, title, created_at) VALUES (?, ?, ?)',
        (user_email, title, datetime.now(timezone.utc).isoformat())
    )
    conn.commit()
    conversation_id = cursor.lastrowid
    conn.close()
    return conversation_id

def get_user_conversations(user_email):
    conn = get_db()
    rows = conn.execute(
        'SELECT id, title, created_at FROM conversations WHERE user_email = ? ORDER BY created_at DESC',
        (user_email,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_conversation(conversation_id, user_email):
    conn = get_db()
    row = conn.execute(
        'SELECT * FROM conversations WHERE id = ? AND user_email = ?',
        (conversation_id, user_email)
    ).fetchone()
    conn.close()
    return row

def save_message(conversation_id, role, content):
    conn = get_db()
    conn.execute(
        'INSERT INTO messages (conversation_id, role, content, created_at) VALUES (?, ?, ?, ?)',
        (conversation_id, role, content, datetime.now(timezone.utc).isoformat())
    )
    conn.commit()
    conn.close()

def get_conversation_messages(conversation_id):
    conn = get_db()
    rows = conn.execute(
        'SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY id ASC',
        (conversation_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]