"""UserRole enumeration value object."""

from enum import Enum


class UserRole(str, Enum):
    """
    User role enumeration.
    Defines authorization levels in the system.
    """
    USER = "user"           # Regular users - can submit ratings
    OPERATOR = "operator"   # Station operators - report malfunctions
    ADMIN = "admin"         # System administrators - approve operators
    
    @classmethod
    def from_string(cls, role_str: str) -> "UserRole":
        """Convert string to UserRole enum."""
        try:
            return cls(role_str.lower())
        except ValueError:
            raise ValueError(f"Invalid role: {role_str}. Must be one of: user, operator, admin")
    
    def requires_approval(self) -> bool:
        """Check if this role requires admin approval before access."""
        return self == UserRole.OPERATOR
    
    def is_admin(self) -> bool:
        """Check if role has admin privileges."""
        return self == UserRole.ADMIN
