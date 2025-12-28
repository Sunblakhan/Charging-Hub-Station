from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ReviewPublished:
    rating_id: str
    station_label: str
    visible_from: datetime

