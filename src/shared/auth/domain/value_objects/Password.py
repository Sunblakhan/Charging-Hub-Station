"""Password value object with hashing logic."""

from dataclasses import dataclass
import hashlib


class WeakPasswordError(Exception):
    """Raised when password doesn't meet security requirements."""
    pass


@dataclass(frozen=True)
class Password:
    """
    Password value object with hashing and validation.
    Stores only hashed version for security.
    """
    hashed_value: str

    @staticmethod
    def from_plain_text(plain_password: str) -> "Password":
        """
        Factory method to create Password from plain text.
        Validates strength and hashes before storage.
        """
        # Check if empty
        if not plain_password or not plain_password.strip():
            raise WeakPasswordError("Password cannot be empty")
        # Validate minimum length
        if len(plain_password) < 6:
            raise WeakPasswordError("Password must be at least 6 characters")
        
        # Hash using SHA-256
        hashed = hashlib.sha256(plain_password.encode()).hexdigest()
        return Password(hashed_value=hashed)
    
    @staticmethod
    def from_hash(hashed_password: str) -> "Password":
        """Factory method to reconstitute Password from stored hash."""
        return Password(hashed_value=hashed_password)
    
    def verify(self, plain_password: str) -> bool:
        """Verify if plain text password matches this hashed password."""
        candidate_hash = hashlib.sha256(plain_password.encode()).hexdigest()
        return candidate_hash == self.hashed_value
