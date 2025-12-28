from uuid import UUID

from src.malfunction.domain.aggregates import IncidentAggregate
from src.malfunction.domain.value_objects.Name import Name
from src.malfunction.domain.value_objects.Email import Email
from src.malfunction.domain.value_objects.StationLabel import StationLabel
from src.malfunction.domain.value_objects.ProblemDescription import ProblemDescription
from src.malfunction.infrastructure.repositories.IncidentRepository import IncidentRepository


class MalfunctionService:
    """
    Application service orchestrating the malfunction use case.
    """

    def __init__(self, incident_repo: IncidentRepository):
        self._incident_repo = incident_repo

    def submit_report(
        self,
        reporter_name: str,
        reporter_email: str,
        station_label: str,
        description: str,
    ) -> UUID:
        """
        Create a new incident via aggregate and persist it.
        """
        aggregate = IncidentAggregate.open(
            reporter_name=Name(reporter_name),
            reporter_email=Email(reporter_email),
            station_label=StationLabel(station_label),
            description=ProblemDescription(description),
        )

        self._incident_repo.save(aggregate.incident)
        # you could also dispatch aggregate.domain_events here if needed
        return aggregate.incident.id

    def validate_report(self, incident_id: UUID) -> None:
        """
        Admin verifies report; aggregate enforces 10‑points rule.
        """
        incident = self._incident_repo.get_by_id(incident_id)
        if incident is None:
            raise ValueError("Incident not found")

        aggregate = IncidentAggregate(incident=incident)
        aggregate.validate_report()  # adds 10 points and events
        self._incident_repo.save(aggregate.incident)

    def resolve_report(self, incident_id: UUID, solution_text: str) -> None:
        """
        Admin/operator resolves the malfunction.
        """
        incident = self._incident_repo.get_by_id(incident_id)
        if incident is None:
            raise ValueError("Incident not found")

        aggregate = IncidentAggregate(incident=incident)
        aggregate.resolve(solution_text=solution_text)
        self._incident_repo.save(aggregate.incident)
