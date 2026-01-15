"""Domain-specific validation exceptions for value objects."""


class InvalidEmail(Exception):
    """Raised when email format is invalid."""
    pass


class InvalidStationLabel(Exception):
    """Raised when station is not in Berlin or doesn't have proper address format."""
    pass


class InvalidProblemDescription(Exception):
    """Raised when problem description is empty or exceeds max length."""
    pass
