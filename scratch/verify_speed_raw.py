import sqlite3
import os

def check_raw_data():
    db_path = r"e:\_Mike-Developer\_mikedev-Windews\trees_bot_v6\trees_bot.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. ดูจำนวนข้อมูลทั้งหมด
    cursor.execute("SELECT COUNT(*) FROM tree_logs")
    total_count = cursor.fetchone()[0]
    
    # 2. ดูความเร็วเฉลี่ย
    cursor.execute("SELECT AVG(duration_sec) FROM tree_logs")
    avg_sec = cursor.fetchone()[0]
    
    # 3. ดูข้อมูล 10 รายการล่าสุด
    cursor.execute("SELECT duration_sec, created_at FROM tree_logs ORDER BY id DESC LIMIT 10")
    recent = cursor.fetchall()
    
    print(f"Total Logs: {total_count}")
    print(f"Average Duration: {avg_sec:.2f} sec/tree")
    print(f"Calculated Speed: {60/avg_sec if avg_sec else 0:.2f} trees/min")
    print("\nRecent 10 logs:")
    for row in recent:
        print(f" - {row['duration_sec']} sec (at {row['created_at']})")
        
    conn.close()

if __name__ == "__main__":
    check_raw_data()
