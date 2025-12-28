from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class SolutionProvided:
    incident_id: UUID
    occurred_at: datetime
    solution_text: str
