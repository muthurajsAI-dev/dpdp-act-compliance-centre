import sqlite3
import os
import json
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), 'app_data.db')
DPDP_SECTIONS_PATH = os.path.join(os.path.dirname(__file__), 'data', 'dpdp_sections.json')
_dpdp_sections_cache = None

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

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
    conn.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            filename TEXT NOT NULL,
            summary TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            type TEXT NOT NULL DEFAULT 'info',
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            is_read INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
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

def save_audit(user_email, filename, summary):
    conn = get_db()
    conn.execute(
        'INSERT INTO audit_logs (user_email, filename, summary, created_at) VALUES (?, ?, ?, ?)',
        (user_email, filename, summary, datetime.now(timezone.utc).isoformat())
    )
    conn.commit()
    conn.close()

def get_user_audits(user_email):
    conn = get_db()
    rows = conn.execute(
        'SELECT filename, summary, created_at FROM audit_logs WHERE user_email = ? ORDER BY created_at DESC',
        (user_email,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_password(email, new_password_hash):
    conn = get_db()
    conn.execute(
        'UPDATE users SET password_hash = ? WHERE email = ?',
        (new_password_hash, email)
    )
    conn.commit()
    conn.close()

def delete_user_account(email):
    conn = get_db()
    conversation_ids = [row['id'] for row in conn.execute(
        'SELECT id FROM conversations WHERE user_email = ?', (email,)
    ).fetchall()]
    for cid in conversation_ids:
        conn.execute('DELETE FROM messages WHERE conversation_id = ?', (cid,))
    conn.execute('DELETE FROM conversations WHERE user_email = ?', (email,))
    conn.execute('DELETE FROM audit_logs WHERE user_email = ?', (email,))
    conn.execute('DELETE FROM users WHERE email = ?', (email,))
    conn.commit()
    conn.close()

def init_chat_db():
    conn = sqlite3.connect('your_database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def create_notification(user_email, title, message, type='info'):
    conn = get_db()
    conn.execute(
        'INSERT INTO notifications (user_email, type, title, message, is_read, created_at) VALUES (?, ?, ?, ?, 0, ?)',
        (user_email, type, title, message, datetime.now(timezone.utc).isoformat())
    )
    conn.commit()
    conn.close()

def get_user_notifications(user_email, limit=20):
    conn = get_db()
    rows = conn.execute(
        'SELECT id, type, title, message, is_read, created_at FROM notifications WHERE user_email = ? ORDER BY created_at DESC LIMIT ?',
        (user_email, limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_unread_notification_count(user_email):
    conn = get_db()
    row = conn.execute(
        'SELECT COUNT(*) as cnt FROM notifications WHERE user_email = ? AND is_read = 0',
        (user_email,)
    ).fetchone()
    conn.close()
    return row['cnt']

def mark_notification_read(notification_id, user_email):
    conn = get_db()
    conn.execute(
        'UPDATE notifications SET is_read = 1 WHERE id = ? AND user_email = ?',
        (notification_id, user_email)
    )
    conn.commit()
    conn.close()

def mark_all_notifications_read(user_email):
    conn = get_db()
    conn.execute('UPDATE notifications SET is_read = 1 WHERE user_email = ?', (user_email,))
    conn.commit()
    conn.close()

def load_dpdp_sections():
    global _dpdp_sections_cache
    if _dpdp_sections_cache is None:
        try:
            with open(DPDP_SECTIONS_PATH, 'r', encoding='utf-8') as f:
                _dpdp_sections_cache = json.load(f)
        except Exception:
            _dpdp_sections_cache = []
    return _dpdp_sections_cache

def search_dpdp_sections(query, limit=5):
    query = query.lower().strip()
    if not query:
        return []
    sections = load_dpdp_sections()
    matches = []
    for sec in sections:
        haystack = f"{sec['title']} {sec['text']}".lower()
        if query in haystack or query in sec['section'].lower():
            matches.append(sec)
    return matches[:limit]