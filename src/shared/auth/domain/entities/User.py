"""User entity - Rich domain model for authentication."""

from dataclasses import dataclass
from typing import Optional

from src.shared.auth.domain.value_objects.Email import Email
from src.shared.auth.domain.value_objects.Password import Password
from src.shared.auth.domain.value_objects.UserRole import UserRole
from src.shared.auth.domain.exceptions import UserNotApprovedError, UnauthorizedError


@dataclass
class User:
    """
    User entity with rich domain behavior.
    Represents an authenticated user in the system.
    """
    email: Email
    password: Password
    role: UserRole
    is_approved: bool = False
    station_label: Optional[str] = None  # Only for operators
    
    def authenticate(self, plain_password: str) -> bool:
        """Verify password matches stored hash."""
        return self.password.verify(plain_password)
    
    def can_access_system(self) -> bool:
        """Check if user has access (approved or doesn't need approval)."""
        if self.role.requires_approval():
            return self.is_approved
        return True
    
    def require_approval(self) -> None:
        """
        Enforce approval requirement before system access.
        Raises exception if user needs approval but doesn't have it.
        """
        if not self.can_access_system():
            raise UserNotApprovedError(
                f"Account pending approval. Contact admin at {SUPER_ADMIN_EMAIL}"
            )
    
    def approve(self) -> None:
        """Approve user for system access (admin action)."""
        if not self.role.requires_approval():
            return  # Already approved by default
        self.is_approved = True
    
    def has_station(self) -> bool:
        """Check if operator has assigned station."""
        return self.station_label is not None
    
    def require_admin(self) -> None:
        """Enforce admin-only operations."""
        if not self.role.is_admin():
            raise UnauthorizedError("This operation requires admin privileges")
    
    @staticmethod
    def create_user(email: str, plain_password: str, role_str: str, station_label: Optional[str] = None) -> "User":
        """
        Factory method to create new user.
        Enforces business rules:
        - Operators must have station
        - Regular users auto-approved
        - Operators need approval
        """
        email_vo = Email(email)
        password_vo = Password.from_plain_text(plain_password)
        role_vo = UserRole.from_string(role_str)
        
        # Business rule: Operators must select station
        if role_vo == UserRole.OPERATOR and not station_label:
            raise ValueError("Operators must select a charging station")
        
        # Business rule: Regular users are auto-approved
        is_approved = not role_vo.requires_approval()
        
        # Business rule: Super admin auto-approved
        if email_vo.value == SUPER_ADMIN_EMAIL:
            is_approved = True
        
        return User(
            email=email_vo,
            password=password_vo,
            role=role_vo,
            is_approved=is_approved,
            station_label=station_label
        )


# Constant for super admin
SUPER_ADMIN_EMAIL = "admin@berlin.de"
