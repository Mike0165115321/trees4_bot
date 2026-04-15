import sqlite3
import os

def check_recent_average():
    db_path = r"e:\_Mike-Developer\_mikedev-Windews\trees_bot_v6\trees_bot.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # ดูความเร็วเฉลี่ยของ 100 รายการล่าสุด
    cursor.execute("SELECT AVG(duration_sec) FROM (SELECT duration_sec FROM tree_logs ORDER BY id DESC LIMIT 100)")
    avg_recent_100 = cursor.fetchone()[0]
    
    # ดูความเร็วเฉลี่ยของ 50 รายการล่าสุด
    cursor.execute("SELECT AVG(duration_sec) FROM (SELECT duration_sec FROM tree_logs ORDER BY id DESC LIMIT 50)")
    avg_recent_50 = cursor.fetchone()[0]
    
    print(f"Average (Last 100): {avg_recent_100:.2f} sec/tree -> {60/avg_recent_100:.2f} trees/min")
    print(f"Average (Last 50): {avg_recent_50:.2f} sec/tree -> {60/avg_recent_50:.2f} trees/min")
    print(f"Potential Hourly: {3600/avg_recent_50:.0f} trees/hour")
    
    conn.close()

if __name__ == "__main__":
    check_recent_average()
