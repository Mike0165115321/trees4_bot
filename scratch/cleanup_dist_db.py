
import sqlite3
import os

# Target the database in the dist folder
DB_FILE = r"e:\_Mike-Developer\_mikedev-Windews\trees_bot_v6\dist\TreesBot_App_v1.0.0\trees_bot.db"

def cleanup():
    if not os.path.exists(DB_FILE):
        print(f"Error: Database not found at {DB_FILE}")
        return

    conn = sqlite3.connect(DB_FILE, isolation_level=None)
    cursor = conn.cursor()
    
    # Get active accounts
    cursor.execute("SELECT id, phone FROM accounts")
    active_accounts = cursor.fetchall()
    active_ids = [str(a[0]) for a in active_accounts]
    id_list_str = ",".join(active_ids)
    
    print(f"Active Accounts Found: {len(active_accounts)} ({', '.join([a[1] for a in active_accounts])})")
    print("-" * 50)

    # Before counts
    cursor.execute("SELECT COUNT(*) FROM tree_logs")
    logs_before = cursor.fetchone()[0]
    cursor.execute("SELECT AVG(duration_sec) FROM tree_logs")
    avg_before = cursor.fetchone()[0] or 0
    
    print(f"Logs before: {logs_before} (Avg: {avg_before:.2f}s)")

    # Execute cleanup
    if active_ids:
        # Delete logs for non-existent accounts
        cursor.execute(f"DELETE FROM tree_logs WHERE account_id NOT IN ({id_list_str})")
        logs_deleted = cursor.rowcount
        
        # Delete analytics for non-existent accounts
        cursor.execute(f"DELETE FROM bot_analytics WHERE account_id NOT IN ({id_list_str})")
        analytics_deleted = cursor.rowcount
        
        # Delete images for non-existent accounts
        cursor.execute(f"DELETE FROM images WHERE account_id NOT IN ({id_list_str})")
        images_deleted = cursor.rowcount
        
        print(f"Cleanup complete:")
        print(f"- Deleted {logs_deleted} orphaned logs")
        print(f"- Deleted {analytics_deleted} orphaned analytics")
        print(f"- Deleted {images_deleted} orphaned images")
    else:
        print("Warning: No active accounts found. Skipping deletion to prevent data loss.")

    # Vacuum
    print("Optimizing database (VACUUM)...")
    try:
        cursor.execute("VACUUM")
    except Exception as e:
        print(f"Warning: VACUUM failed: {e}")
    
    # After counts
    cursor.execute("SELECT COUNT(*) FROM tree_logs")
    logs_after = cursor.fetchone()[0]
    cursor.execute("SELECT AVG(duration_sec) FROM tree_logs")
    avg_after = cursor.fetchone()[0] or 0
    
    print("-" * 50)
    print(f"Logs after: {logs_after} (Avg: {avg_after:.2f}s)")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    cleanup()
