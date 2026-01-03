import os

# Define the file content
files = {
    "src/auth/__init__.py": "",
    
    "src/auth/user_model.py": """
from dataclasses import dataclass

@dataclass
class User:
    email: str
    password_hash: str
    role: str  # 'user', 'operator', 'admin'
    is_approved: bool = False
""",

    "src/auth/auth_handler.py": """
import sqlite3
import hashlib
import re
from src.auth.user_model import User

DB_FILE = "users.db"
SUPER_ADMIN = "admin@berlin.de"  # HARDCODED SUPER ADMIN

class AuthHandler:
    def __init__(self):
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute(\"\"\"CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY, password TEXT, role TEXT, approved INTEGER)\"\"\")

    def _hash(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def login(self, email, password):
        with sqlite3.connect(DB_FILE) as conn:
            cur = conn.cursor()
            cur.execute("SELECT email, password, role, approved FROM users WHERE email=?", (email,))
            row = cur.fetchone()
            
        if not row: return None, "User not found"
        if row[1] != self._hash(password): return None, "Wrong password"
        if not row[3]: return None, "Account pending approval"
        
        return User(email=row[0], password_hash=row[1], role=row[2], is_approved=bool(row[3])), "Success"

    def signup(self, email, password, role):
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email): return False, "Invalid Email"
        
        hashed = self._hash(password)
        is_approved = True if role == 'user' or email == SUPER_ADMIN else False
        
        try:
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("INSERT INTO users VALUES (?, ?, ?, ?)", 
                             (email, hashed, role, int(is_approved)))
            return True, "Signup successful! Log in now." if is_approved else "Signup successful! Wait for Admin approval."
        except sqlite3.IntegrityError:
            return False, "Email already exists"

    def get_pending_operators(self):
        with sqlite3.connect(DB_FILE) as conn:
            rows = conn.execute("SELECT email FROM users WHERE role='operator' AND approved=0").fetchall()
        return [r[0] for r in rows]

    def approve_operator(self, email):
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("UPDATE users SET approved=1 WHERE email=?", (email,))
""",

    "src/auth/ui_auth.py": """
import streamlit as st
from src.auth.auth_handler import AuthHandler

def render_login():
    st.title("🔐 Login to Berlin Geo Heatmap")
    
    handler = AuthHandler()
    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        email = st.text_input("Email", key="l_mail")
        password = st.text_input("Password", type="password", key="l_pass")
        if st.button("Login"):
            user, msg = handler.login(email, password)
            if user:
                st.session_state['user'] = user
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

    with tab2:
        email = st.text_input("Email", key="s_mail")
        password = st.text_input("Password", type="password", key="s_pass")
        role = st.selectbox("Role", ["user", "operator"], key="s_role")
        if st.button("Sign Up"):
            success, msg = handler.signup(email, password, role)
            if success: st.success(msg)
            else: st.error(msg)
"""
}

# Create folders and write files
for path, content in files.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip())

print("✅ Authentication module created successfully inside src/auth/")