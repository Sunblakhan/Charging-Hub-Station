# src/rating/domain/value_objects/ReviewText.py
from dataclasses import dataclass
from typing import Optional


MAX_REVIEW_LENGTH = 500


@dataclass(frozen=True)
class ReviewText:
    value: Optional[str]

    def __post_init__(self) -> None:
        if self.value is None:
            return
        text = self.value.strip()
        if text == "":
            # treat empty as no review; you can also choose to allow empty explicitly
            object.__setattr__(self, "value", None)
            return
        if len(text) > MAX_REVIEW_LENGTH:
            raise ValueError("Review text is too long")
        object.__setattr__(self, "value", text)
