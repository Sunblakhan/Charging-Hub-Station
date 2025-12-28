from dataclasses import dataclass

MIN_NAME_LENGTH = 2
MAX_NAME_LENGTH = 100


@dataclass(frozen=True)
class Name:
    value: str

    def __post_init__(self) -> None:
        text = self.value.strip()
        if text == "":
            raise ValueError("Name must not be empty")
        if len(text) < MIN_NAME_LENGTH:
            raise ValueError("Name is too short")
        if len(text) > MAX_NAME_LENGTH:
            raise ValueError("Name is too long")
        object.__setattr__(self, "value", text)
