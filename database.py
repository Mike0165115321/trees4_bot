import sqlite3
import os

DB_FILE = "trees_bot.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """สร้าง Table หากยังไม่มี"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            recorder TEXT NOT NULL,
            surveyor TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            file_path TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY (account_id) REFERENCES accounts (id) ON DELETE CASCADE
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def get_all_accounts():
    conn = get_db_connection()
    accounts = [dict(row) for row in conn.execute('SELECT * FROM accounts').fetchall()]
    conn.close()
    return accounts

def get_pending_accounts():
    conn = get_db_connection()
    accounts = [dict(row) for row in conn.execute("SELECT * FROM accounts WHERE status = 'pending'").fetchall()]
    conn.close()
    return accounts

def add_account(phone, password, recorder, surveyor):
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            'INSERT INTO accounts (phone, password, recorder, surveyor) VALUES (?, ?, ?, ?)',
            (phone, password, recorder, surveyor)
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def add_image(account_id, file_path):
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO images (account_id, file_path) VALUES (?, ?)',
        (account_id, file_path)
    )
    conn.commit()
    conn.close()

def update_status(phone, status):
    conn = get_db_connection()
    conn.execute(
        'UPDATE accounts SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE phone = ?',
        (status, phone)
    )
    conn.commit()
    conn.close()

def delete_account(account_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM images WHERE account_id = ?', (account_id,))
    conn.execute('DELETE FROM accounts WHERE id = ?', (account_id,))
    conn.commit()
    conn.close()

def get_images(account_id):
    conn = get_db_connection()
    images = [dict(row) for row in conn.execute('SELECT * FROM images WHERE account_id = ?', (account_id,)).fetchall()]
    conn.close()
    return images

def delete_image_by_id(image_id):
    conn = get_db_connection()
    # Can also fetch file_path and return it to delete from disk if needed
    cursor = conn.execute('SELECT file_path FROM images WHERE id = ?', (image_id,))
    row = cursor.fetchone()
    file_path = row['file_path'] if row else None
    
    conn.execute('DELETE FROM images WHERE id = ?', (image_id,))
    conn.commit()
    conn.close()
    return file_path

def get_settings():
    conn = get_db_connection()
    rows = conn.execute('SELECT * FROM settings').fetchall()
    conn.close()
    settings = {row['key']: row['value'] for row in rows}
    
    # Defaults if empty
    defaults = {
        "health_3": "80",
        "health_2": "15",
        "health_1": "5",
        "headless": "false"
    }
    for k, v in defaults.items():
        if k not in settings:
            settings[k] = v
    return settings

def update_setting(key, value):
    conn = get_db_connection()
    conn.execute(
        'INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)',
        (key, str(value))
    )
    conn.commit()
    conn.close()

def reset_all_status():
    """รีเซ็ตทุกคนกลับเป็น pending"""
    conn = get_db_connection()
    conn.execute("UPDATE accounts SET status = 'pending'")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized.")
