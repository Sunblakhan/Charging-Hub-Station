from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class RatingSubmitted:
    rating_id: str          # which rating was submitted
    station_label: str         # which station it belongs to
    submitted_at: datetime  
