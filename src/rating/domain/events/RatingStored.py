from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class RatingStored:
    rating_id: str
    station_label: str
    stored_at: datetime

