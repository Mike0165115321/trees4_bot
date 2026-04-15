import sqlite3
import json

def inspect_db():
    conn = sqlite3.connect('trees_bot.db')
    cursor = conn.cursor()
    
    # Get tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"Tables: {tables}")
    
    for table_name in tables:
        table_name = table_name[0]
        print(f"\n--- {table_name} ---")
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        print(f"Columns: {columns}")
        
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 5;")
        rows = cursor.fetchall()
        print(f"Sample rows: {rows}")

    # Check for specific performance related data if likely
    # Based on the UI description, there might be a logs or performance table
    # Or maybe it's calculated from accounts 'done' timestamp?
    # Let's check for account completion times
    
    conn.close()

if __name__ == "__main__":
    inspect_db()
