from uuid import uuid4
from typing import List

from src.malfunction.domain.entities.Incident import Incident
from src.malfunction.infrastructure.repositories.IncidentRepository import IncidentRepository
from src.malfunction.domain.value_objects.Name import Name
from src.malfunction.domain.value_objects.Email import Email
from src.malfunction.domain.value_objects.StationLabel import StationLabel
from src.malfunction.domain.value_objects.ProblemDescription import ProblemDescription


class MalfunctionService:
    def __init__(self, repository: IncidentRepository):
        self._repository = repository

    # --- UPDATED METHOD: Accepts is_valid (defaults to False) ---
    def submit_report(self, reporter_name: str, reporter_email: str, station_label: str, description: str, is_valid: bool = False) -> str:
        """
        Creates a new incident report.
        is_valid: If True, the report is considered valid immediately (for Operators).
        """
        incident_id = uuid4()
        
        # Determine status string
        initial_status = "IN_PROGRESS" if is_valid else "PENDING"

        # Create the Domain Entity
        incident = Incident(
            id=incident_id,
            reporter_name=Name(reporter_name),
            reporter_email=Email(reporter_email),
            station_label=StationLabel(station_label),
            description=ProblemDescription(description),
            is_valid=is_valid,  # Uses the parameter passed in
            is_solved=False,    # Always starts as unsolved
            points_awarded=0,
            status=initial_status
        )
        
        self._repository.save(incident)
        return str(incident_id)

    def get_incidents_for_station(self, station_label: str) -> List[Incident]:
        return list(self._repository.get_by_station(station_label))

    def get_all_incidents(self) -> List[Incident]:
        return list(self._repository.get_all())

    def update_incident_status(self, incident_id: str, is_valid: bool, is_solved: bool) -> None:
        self._repository.update_status(incident_id, is_valid, is_solved)