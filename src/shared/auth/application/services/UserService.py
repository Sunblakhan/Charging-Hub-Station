"""User management application service."""

from typing import List, Tuple

from src.shared.auth.domain.value_objects.Email import Email
from src.shared.auth.infrastructure.repositories.UserRepository import UserRepositoryInterface


class UserService:
    """
    Application service for user management use cases.
    Used by admin panel for operator approval/rejection.
    """
    
    def __init__(self, user_repository: UserRepositoryInterface):
        self._user_repo = user_repository
    
    def get_pending_operators(self) -> List[Tuple[str, str]]:
        """
        Get all operators awaiting approval.
        
        Returns:
            List of (email, station_label) tuples
        """
        return self._user_repo.get_pending_operators()
    
    def approve_operator(self, email_str: str) -> bool:
        """
        Approve operator account for system access.
        
        Returns:
            True if approval successful, False otherwise
        """
        email = Email(email_str)
        return self._user_repo.approve_operator(email)
    
    def reject_operator(self, email_str: str) -> bool:
        """
        Reject and delete operator registration.
        
        Returns:
            True if deletion successful, False otherwise
        """
        email = Email(email_str)
        return self._user_repo.delete_user(email)
