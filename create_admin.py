import sqlite3
import hashlib

DB_FILE = "users.db"

def create_super_admin():
    email = "admin@berlin.de"
    password = "123"  # <--- You can change this password
    role = "admin"
    
    # Hash the password just like the app does
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    # Connect to the database
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        
        try:
            # Insert the Admin User
            # columns: email, password, role, approved (1=True), station_label (None)
            cursor.execute("""
                INSERT INTO users (email, password, role, approved, station_label)
                VALUES (?, ?, ?, ?, ?)
            """, (email, password_hash, role, 1, None))
            
            print(f"✅ SUCCESS: Created Admin user '{email}' with password '{password}'")
            
        except sqlite3.IntegrityError:
            print("⚠️ User already exists. Updating role to 'admin'...")
            cursor.execute("""
                UPDATE users 
                SET role='admin', approved=1 
                WHERE email=?
            """, (email,))
            print("✅ SUCCESS: Updated existing user to Admin.")

if __name__ == "__main__":
    create_super_admin()