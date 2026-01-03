import sqlite3
import hashlib
import re
from dataclasses import dataclass

DB_FILE = "users.db"
SUPER_ADMIN = "admin@berlin.de"

@dataclass
class User:
    email: str
    password_hash: str
    role: str
    is_approved: bool = False
    station_label: str = None  # <--- NEW FIELD

class AuthHandler:
    def __init__(self):
        self._init_db()

    def _init_db(self):
        """Creates the users table with the new 'station_label' column."""
        with sqlite3.connect(DB_FILE) as conn:
            # We add 'station_label TEXT' to store the operator's station
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    email TEXT PRIMARY KEY, 
                    password TEXT, 
                    role TEXT, 
                    approved INTEGER,
                    station_label TEXT 
                )
            """)

    def _hash(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def login(self, email, password):
        with sqlite3.connect(DB_FILE) as conn:
            cur = conn.cursor()
            # We now select station_label as well (row[4])
            cur.execute("SELECT email, password, role, approved, station_label FROM users WHERE email=?", (email,))
            row = cur.fetchone()
            
        if not row: return None, "User not found"
        if row[1] != self._hash(password): return None, "Wrong password"
        if not row[3]: return None, "Account pending approval"
        
        return User(
            email=row[0], 
            password_hash=row[1], 
            role=row[2], 
            is_approved=bool(row[3]),
            station_label=row[4] # <--- Pass this to the User object
        ), "Success"

    # UPDATED SIGNUP METHOD
    def signup(self, email, password, role, station_label=None):
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email): return False, "Invalid Email"
        
        hashed = self._hash(password)
        is_approved = True if role == 'user' or email == SUPER_ADMIN else False
        
        # Ensure operators have selected a station
        if role == 'operator' and not station_label:
            return False, "Operators must select a station."

        try:
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute(
                    "INSERT INTO users VALUES (?, ?, ?, ?, ?)", 
                    (email, hashed, role, int(is_approved), station_label)
                )
            return True, "Signup successful!"
        except sqlite3.IntegrityError:
            return False, "Email already exists"

    # In src/auth/auth_handler.py

    def get_pending_operators(self):
        """Returns a list of tuples: [(email, station_label), ...]"""
        with sqlite3.connect(DB_FILE) as conn:
            # Fetch both email AND station_label
            rows = conn.execute("SELECT email, station_label FROM users WHERE role='operator' AND approved=0").fetchall()
        return rows # Returns list of tuples like [('hans@gmail.com', 'Lidl - Berlin'), ...]

    def reject_operator(self, email):
        """Deletes the user request permanently."""
        try:
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("DELETE FROM users WHERE email=?", (email,))
            return True
        except Exception as e:
            print(f"Error rejecting: {e}")
            return False

    # Keep approve_operator the same
    def approve_operator(self, email):
        try:
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("UPDATE users SET approved=1 WHERE email=?", (email,))
            return True
        except Exception:
            return False