from dataclasses import dataclass, field
from uuid import UUID, uuid4

from src.malfunction.domain.value_objects.Email import Email
from src.malfunction.domain.value_objects.Name import Name
from src.malfunction.domain.value_objects.StationLabel import StationLabel
from src.malfunction.domain.value_objects.ProblemDescription import ProblemDescription


@dataclass
class Incident:
    """
    Entity representing one malfunction report.
    """

    reporter_name: Name
    reporter_email: Email
    station_label: StationLabel
    description: ProblemDescription
    id: UUID = field(default_factory=uuid4)
    is_valid: bool = False
    is_solved: bool = False
    points_awarded: int = 0
    status: str = "PENDING"  # PENDING, PUBLISHED, RESOLVED
