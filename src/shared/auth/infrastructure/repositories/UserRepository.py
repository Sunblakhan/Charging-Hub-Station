"""User repository interface and SQLite implementation."""

import sqlite3
from abc import ABC, abstractmethod
from typing import Optional, List

from src.shared.auth.domain.entities.User import User
from src.shared.auth.domain.value_objects.Email import Email
from src.shared.auth.domain.value_objects.Password import Password
from src.shared.auth.domain.value_objects.UserRole import UserRole


class UserRepositoryInterface(ABC):
    """Repository interface for User persistence."""
    
    @abstractmethod
    def save(self, user: User) -> None:
        """Persist user to storage."""
        ...
    
    @abstractmethod
    def find_by_email(self, email: Email) -> Optional[User]:
        """Retrieve user by email."""
        ...
    
    @abstractmethod
    def get_pending_operators(self) -> List[tuple]:
        """Get all operators awaiting approval."""
        ...
    
    @abstractmethod
    def approve_operator(self, email: Email) -> bool:
        """Approve operator account."""
        ...
    
    @abstractmethod
    def delete_user(self, email: Email) -> bool:
        """Delete user account."""
        ...


class SqliteUserRepository(UserRepositoryInterface):
    """SQLite implementation of User repository."""
    
    def __init__(self, db_path: str = "users.db"):
        self._db_path = db_path
        self._ensure_schema()
    
    def _ensure_schema(self) -> None:
        """Create users table if it doesn't exist."""
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    email TEXT PRIMARY KEY,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL,
                    approved INTEGER NOT NULL DEFAULT 0,
                    station_label TEXT
                )
            """)
            conn.commit()
    
    def save(self, user: User) -> None:
        """Insert or update user in database."""
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO users (email, password, role, approved, station_label)
                VALUES (?, ?, ?, ?, ?)
            """, (
                user.email.value,
                user.password.hashed_value,
                user.role.value,
                int(user.is_approved),
                user.station_label
            ))
            conn.commit()
    
    def find_by_email(self, email: Email) -> Optional[User]:
        """Retrieve user by email from database."""
        with sqlite3.connect(self._db_path) as conn:
            row = conn.execute("""
                SELECT email, password, role, approved, station_label
                FROM users WHERE email = ?
            """, (email.value,)).fetchone()
        
        if not row:
            return None
        
        return User(
            email=Email(row[0]),
            password=Password.from_hash(row[1]),
            role=UserRole.from_string(row[2]),
            is_approved=bool(row[3]),
            station_label=row[4]
        )
    
    def get_pending_operators(self) -> List[tuple]:
        """Get list of (email, station_label) for pending operators."""
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute("""
                SELECT email, station_label
                FROM users
                WHERE role = 'operator' AND approved = 0
            """).fetchall()
        return rows
    
    def approve_operator(self, email: Email) -> bool:
        """Approve operator by email."""
        try:
            with sqlite3.connect(self._db_path) as conn:
                conn.execute("""
                    UPDATE users SET approved = 1
                    WHERE email = ?
                """, (email.value,))
                conn.commit()
            return True
        except (sqlite3.DatabaseError, sqlite3.IntegrityError) as e:
            print(f"Database error while approving operator: {e}")
            return False
    
    def delete_user(self, email: Email) -> bool:
        """Delete user by email."""
        try:
            with sqlite3.connect(self._db_path) as conn:
                conn.execute("DELETE FROM users WHERE email = ?", (email.value,))
                conn.commit()
            return True
        except (sqlite3.DatabaseError, sqlite3.IntegrityError) as e:
            print(f"Database error while deleting user: {e}")
            return False
