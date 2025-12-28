from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class RatingValidated:
    rating_id: str
    is_valid: bool
    reason: str | None
    validated_at: datetime

