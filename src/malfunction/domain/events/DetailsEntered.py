from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class DetailsEntered:
    incident_id: UUID
    occurred_at: datetime
