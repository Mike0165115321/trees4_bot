
import sqlite3
import os

DB_FILE = r"e:\_Mike-Developer\_mikedev-Windews\trees_bot_v6\trees_bot.db"

def analyze():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Total count
    cursor.execute("SELECT COUNT(*) FROM tree_logs")
    total = cursor.fetchone()[0]
    
    # First 100
    cursor.execute("SELECT AVG(duration_sec), MIN(id), MAX(id) FROM (SELECT * FROM tree_logs ORDER BY id ASC LIMIT 100)")
    avg100, min100, max100 = cursor.fetchone()
    
    # First 200
    cursor.execute("SELECT AVG(duration_sec), MIN(id), MAX(id) FROM (SELECT * FROM tree_logs ORDER BY id ASC LIMIT 200)")
    avg200, min200, max200 = cursor.fetchone()
    
    # The rest (after 200)
    cursor.execute("SELECT AVG(duration_sec) FROM tree_logs WHERE id > 200")
    avg_rest = cursor.fetchone()[0]
    
    print(f"Total trees in logs: {total}")
    print(f"First 100 (IDs {min100}-{max100}): Average {avg100:.2f} sec")
    print(f"First 200 (IDs {min200}-{max200}): Average {avg200:.2f} sec")
    if avg_rest:
        print(f"The rest (IDs > 200): Average {avg_rest:.2f} sec")
    
    conn.close()

if __name__ == "__main__":
    analyze()
