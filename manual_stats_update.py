import sqlite3
import os

DB_FILE = "trees_bot.db"

def update_manual_stats():
    print("\n" + "="*40)
    print("   Trees4All - Manual Stats System")
    print("="*40)
    
    phone = input("\n📱 Enter Phone Number to Update: ").strip()
    
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    acc = conn.execute("SELECT * FROM accounts WHERE phone = ?", (phone,)).fetchone()
    
    if not acc:
        print(f"❌ Account {phone} not found!")
        conn.close()
        return

    print(f"✅ Found: {acc['phone']} ({acc['recorder']})")
    print(f"   Current: {acc['trees_filled']} Trees / {acc['images_uploaded']} Images")
    
    try:
        new_trees = input(f"\nEnter new Tree Count [{acc['trees_filled']}]: ")
        new_trees = int(new_trees) if new_trees else acc['trees_filled']
        
        new_imgs = input(f"Enter new Image Count [{acc['images_uploaded']}]: ")
        new_imgs = int(new_imgs) if new_imgs else acc['images_uploaded']
        
        conn.execute("""
            UPDATE accounts 
            SET trees_filled = ?, images_uploaded = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE phone = ?
        """, (new_trees, new_imgs, phone))
        
        conn.commit()
        print(f"\n✨ Update Successful! Refresh Dashboard to see changes.")
        
    except ValueError:
        print("❌ Error: Please enter numbers only.")
    finally:
        conn.close()

if __name__ == "__main__":
    if not os.path.exists(DB_FILE):
        print(f"❌ Database {DB_FILE} not found!")
    else:
        while True:
            update_manual_stats()
            cont = input("\nUpdate another? (y/n): ").lower()
            if cont != 'y':
                break
