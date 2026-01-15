"""Email value object - Shared across all bounded contexts."""

from dataclasses import dataclass
import re


class InvalidEmail(Exception):
    """Raised when email format is invalid."""
    pass


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(frozen=True)
class Email:
    """
    Email value object with validation and normalization.
    Shared across Rating, Malfunction, and Auth contexts.
    """
    value: str

    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise InvalidEmail("Email cannot be empty")
        normalized = self.value.strip().lower()
        if not EMAIL_PATTERN.match(normalized):
            raise InvalidEmail(f"Invalid email format")
        object.__setattr__(self, "value", normalized)
