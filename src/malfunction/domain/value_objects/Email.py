from dataclasses import dataclass
import re

from src.malfunction.domain.exceptions import InvalidEmail


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(frozen=True)
class Email:
    value: str

    def __post_init__(self):
        normalized = self.value.strip().lower()
        if not EMAIL_PATTERN.match(normalized):
            raise InvalidEmail(f"Invalid email: {self.value}")
        object.__setattr__(self, "value", normalized)
