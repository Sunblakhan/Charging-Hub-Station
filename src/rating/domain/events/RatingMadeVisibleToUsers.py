from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class RatingMadeVisibleToUsers:
    rating_id: str
    station_label: str
    published_at: datetime

