"""Domain exceptions for authentication and authorization."""


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass


class UnauthorizedError(Exception):
    """Raised when user lacks permission for an operation."""
    pass


class UserNotApprovedError(AuthenticationError):
    """Raised when operator account is pending approval."""
    pass


class InvalidCredentialsError(AuthenticationError):
    """Raised when email/password combination is invalid."""
    pass


class UserAlreadyExistsError(Exception):
    """Raised when attempting to register with existing email."""
    pass
