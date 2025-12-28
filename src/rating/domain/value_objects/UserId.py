from dataclasses import dataclass
from uuid import uuid4


@dataclass(frozen=True)
class UserId:
    value: str

    @staticmethod
    def new() -> "UserId":
        return UserId(str(uuid4()))
