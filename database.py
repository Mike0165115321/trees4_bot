import sqlite3
import os
import sys

def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# For DB, we want it to be in the same folder as the EXE, not in the temp _MEIPASS folder.
# So we use the directory of the executable for the DB.
if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

DB_FILE = os.path.join(APP_DIR, "trees_bot.db")

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
            priority INTEGER DEFAULT 0,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # เพิ่มคอลัมน์ใหม่ถ้ายังไม่มี (migration สำหรับ DB เก่า)
    try:
        cursor.execute('ALTER TABLE accounts ADD COLUMN priority INTEGER DEFAULT 0')
    except: pass
    try:
        cursor.execute('ALTER TABLE accounts ADD COLUMN trees_filled INTEGER DEFAULT 0')
    except: pass
    try:
        cursor.execute('ALTER TABLE accounts ADD COLUMN images_uploaded INTEGER DEFAULT 0')
    except: pass
    try:
        cursor.execute('ALTER TABLE accounts ADD COLUMN health_3 INTEGER DEFAULT 80')
    except: pass
    try:
        cursor.execute('ALTER TABLE accounts ADD COLUMN health_2 INTEGER DEFAULT 15')
    except: pass
    try:
        cursor.execute('ALTER TABLE accounts ADD COLUMN health_1 INTEGER DEFAULT 5')
    except: pass
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
        CREATE TABLE IF NOT EXISTS tree_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            duration_sec REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
    accounts = [dict(row) for row in conn.execute('SELECT * FROM accounts ORDER BY priority DESC, id ASC').fetchall()]
    conn.close()
    return accounts

def get_pending_accounts():
    conn = get_db_connection()
    accounts = [dict(row) for row in conn.execute("SELECT * FROM accounts WHERE status = 'pending' ORDER BY priority DESC, id ASC").fetchall()]
    conn.close()
    return accounts

def move_to_top(account_id):
    """ย้ายบัญชีนี้ขึ้นไปเป็นลำดับแรกในคิว"""
    conn = get_db_connection()
    # หาค่า priority สูงสุดในตอนนี้ แล้วบวก 1
    row = conn.execute('SELECT MAX(priority) FROM accounts').fetchone()
    max_priority = (row[0] or 0) + 1
    conn.execute('UPDATE accounts SET priority = ? WHERE id = ?', (max_priority, account_id))
    conn.commit()
    conn.close()

def add_account(phone, password, recorder, surveyor, health_3=80, health_2=15, health_1=5):
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            'INSERT INTO accounts (phone, password, recorder, surveyor, health_3, health_2, health_1) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (phone, password, recorder, surveyor, health_3, health_2, health_1)
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

def update_status(phone, status, trees_filled=0, images_uploaded=0):
    conn = get_db_connection()
    conn.execute(
        '''UPDATE accounts 
           SET status = ?, 
               trees_filled = ?, 
               images_uploaded = ?, 
               updated_at = CURRENT_TIMESTAMP 
           WHERE phone = ?''',
        (status, trees_filled, images_uploaded, phone)
    )
    conn.commit()
    conn.close()

def delete_account(account_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM images WHERE account_id = ?', (account_id,))
    conn.execute('DELETE FROM accounts WHERE id = ?', (account_id,))
    conn.commit()
    conn.close()

def requeue_account(account_id):
    """รีเซ็ตบัญชีกลับเป็น pending (หยิบกลับเข้าคิว)"""
    conn = get_db_connection()
    conn.execute(
        "UPDATE accounts SET status = 'pending', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (account_id,)
    )
    conn.commit()
    conn.close()

def get_images(account_id):
    conn = get_db_connection()
    images = [dict(row) for row in conn.execute('SELECT * FROM images WHERE account_id = ?', (account_id,)).fetchall()]
    conn.close()
    return images

def get_images(account_id):
    conn = get_db_connection()
    images = [dict(row) for row in conn.execute('SELECT * FROM images WHERE account_id = ?', (account_id,)).fetchall()]
    conn.close()
    return images

def update_image_status(image_id, status):
    conn = get_db_connection()
    conn.execute('UPDATE images SET status = ? WHERE id = ?', (status, image_id))
    conn.commit()
    conn.close()

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

def add_speed_log(account_id, duration_sec):
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO tree_logs (account_id, duration_sec)
        VALUES (?, ?)
    ''', (account_id, duration_sec))
    conn.commit()
    conn.close()

def get_speed_stats(account_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*), AVG(duration_sec) FROM tree_logs WHERE account_id = ?", (account_id,))
    row = cursor.fetchone()
    total_trees = row[0] or 0
    avg_speed = round(row[1] or 0.0, 2)
    
    cursor.execute("SELECT duration_sec FROM tree_logs WHERE account_id = ? ORDER BY id DESC LIMIT 20", (account_id,))
    recent_speeds = [r[0] for r in cursor.fetchall()]
    
    conn.close()
    return {
        "total_trees": total_trees,
        "avg_speed": avg_speed,
        "recent_speeds": recent_speeds
    }

def get_global_speed():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT AVG(duration_sec) FROM tree_logs")
    avg = cursor.fetchone()[0]
    conn.close()
    
    if not avg or avg == 0:
        return {"avg_sec": 0, "per_min": 0, "per_hour": 0}
        
    avg_sec = round(avg, 2)
    per_min = round(60 / avg)
    per_hour = round(3600 / avg)
    
    return {
        "avg_sec": avg_sec,
        "per_min": per_min,
        "per_hour": per_hour
    }

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
        "headless": "false",
        "bot_paused": "false",
        "bot_stop_requested": "false"
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

def retry_error_status():
    """รีเซ็ตเฉพาะคนที่ error กลับเป็น pending"""
    conn = get_db_connection()
    conn.execute("UPDATE accounts SET status = 'pending' WHERE status = 'error'")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized.")
