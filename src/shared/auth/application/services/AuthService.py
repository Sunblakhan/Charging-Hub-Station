"""Authentication application service."""

from typing import Optional

from src.shared.auth.domain.entities.User import User
from src.shared.auth.domain.value_objects.Email import Email, InvalidEmail
from src.shared.auth.domain.exceptions import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
)
from src.shared.auth.infrastructure.repositories.UserRepository import UserRepositoryInterface


class AuthService:
    """
    Application service for authentication use cases.
    Orchestrates login and signup workflows.
    """
    
    def __init__(self, user_repository: UserRepositoryInterface):
        self._user_repo = user_repository
    
    def login(self, email_str: str, plain_password: str) -> User:
        """
        Authenticate user with email and password.
        
        Returns:
            User entity if authentication successful
            
        Raises:
            InvalidEmail: If email format invalid
            InvalidCredentialsError: If email not found or password wrong
            UserNotApprovedError: If operator not yet approved
        """
        if not plain_password or not plain_password.strip():
            raise InvalidCredentialsError("Password cannot be empty")
        # 1. Validate email format
        try:
            email = Email(email_str)
        except InvalidEmail as e:
            raise InvalidCredentialsError(str(e))
        
        # 2. Find user
        user = self._user_repo.find_by_email(email)
        if not user:
            raise InvalidCredentialsError("User not found")
        
        # 3. Verify password
        if not user.authenticate(plain_password):
            raise InvalidCredentialsError("Incorrect password")
        
        # 4. Check approval status
        user.require_approval()
        
        return user
    
    def signup(
        self,
        email_str: str,
        plain_password: str,
        role_str: str,
        station_label: Optional[str] = None
    ) -> User:
        """
        Register new user account.
        
        Returns:
            Created User entity
            
        Raises:
            InvalidEmail: If email format invalid
            WeakPasswordError: If password too weak
            ValueError: If role invalid or operator without station
            UserAlreadyExistsError: If email already registered
        """
        # 1. Check if user already exists
        try:
            email = Email(email_str)
            existing_user = self._user_repo.find_by_email(email)
            if existing_user:
                raise UserAlreadyExistsError(f"Email {email_str} already registered")
        except InvalidEmail:
            # Let User.create_user handle email validation
            pass
        
        # 2. Create user (validates all business rules)
        user = User.create_user(
            email=email_str,
            plain_password=plain_password,
            role_str=role_str,
            station_label=station_label
        )
        
        # 3. Persist to database
        self._user_repo.save(user)
        
        return user
