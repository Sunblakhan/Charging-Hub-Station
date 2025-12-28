from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class IssuesStatusUpdateReport:
    incident_id: UUID
    occurred_at: datetime
    old_status: str
    new_status: str
