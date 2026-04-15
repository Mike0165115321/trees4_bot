import sqlite3
import os

def get_db_connection():
    # Use absolute path for DB to be safe
    db_path = r"e:\_Mike-Developer\_mikedev-Windews\trees_bot_v6\trees_bot.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def get_global_speed():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT AVG(duration_sec) FROM tree_logs")
    avg = cursor.fetchone()[0]
    conn.close()
    
    if not avg or avg == 0:
        return {"avg_sec": 0, "per_min": 0, "per_hour": 0}
        
    avg_sec = round(avg, 2)
    per_min = round(60 / avg, 2) # Use 2 decimals for "WOW" effect
    per_hour = int(3600 / avg)
    
    return {
        "avg_sec": avg_sec,
        "per_min": per_min,
        "per_hour": per_hour
    }

if __name__ == "__main__":
    import json
    print(json.dumps(get_global_speed(), indent=2))
