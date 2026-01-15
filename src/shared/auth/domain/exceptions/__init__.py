"""Domain exceptions for auth shared kernel."""

from .errors import (
    AuthenticationError,
    UnauthorizedError,
    UserNotApprovedError,
    InvalidCredentialsError,
    UserAlreadyExistsError,
)
from ..value_objects.Email import InvalidEmail

__all__ = [
    "AuthenticationError",
    "UnauthorizedError",
    "UserNotApprovedError",
    "InvalidCredentialsError",
    "UserAlreadyExistsError",
    "InvalidEmail",
]
