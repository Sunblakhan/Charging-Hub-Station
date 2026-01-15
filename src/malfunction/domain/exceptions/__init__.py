"""Domain exceptions for Malfunction bounded context."""

from .errors import (
    InvalidEmail,
    InvalidStationLabel,
    InvalidProblemDescription,
)

__all__ = [
    "InvalidEmail",
    "InvalidStationLabel",
    "InvalidProblemDescription",
]
