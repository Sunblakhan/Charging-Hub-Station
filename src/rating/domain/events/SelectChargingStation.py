from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class SelectChargingStation:
    user_id: str
    station_label: str
    selected_at: datetime

