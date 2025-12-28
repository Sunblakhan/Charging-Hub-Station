from dataclasses import dataclass
import re


EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(frozen=True)
class Email:
    value: str

    def __post_init__(self) -> None:
        if not EMAIL_REGEX.match(self.value):
            raise ValueError("Invalid email format")
