from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class NewRatingCreated:
    rating_id: str
    station_label: str
    user_name: str
    user_email: str
    stars: int
    review_text: str
    occurred_at: datetime
