from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class StationsAvgRatingUpdated:
    station_label: str
    new_average: float
    updated_at: datetime

