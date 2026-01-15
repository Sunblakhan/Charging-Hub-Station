from dataclasses import dataclass

from src.malfunction.domain.exceptions import InvalidProblemDescription


@dataclass(frozen=True)
class ProblemDescription:
    value: str

    def __post_init__(self):
        text = self.value.strip()
        if not text:
            raise InvalidProblemDescription("Description cannot be empty")
        if len(text) > 2000:
            raise InvalidProblemDescription("Description too long")
        object.__setattr__(self, "value", text)
