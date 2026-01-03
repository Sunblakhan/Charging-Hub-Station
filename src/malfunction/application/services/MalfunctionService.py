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

    def submit_report(self, reporter_name: str, reporter_email: str, station_label: str, description: str) -> str:
        """
        Creates a new incident report and saves it to the repository.
        """
        incident_id = uuid4()
        
        # Create the Domain Entity
        incident = Incident(
            id=incident_id,
            reporter_name=Name(reporter_name),
            reporter_email=Email(reporter_email),
            station_label=StationLabel(station_label),
            description=ProblemDescription(description),
            is_valid=False,     # Default to False until validated
            is_solved=False,    # Default to False
            points_awarded=0,
            status="PENDING"
        )
        
        self._repository.save(incident)
        return str(incident_id)

    # --- NEW METHODS ADDED BELOW ---

    def get_incidents_for_station(self, station_label: str) -> List[Incident]:
        """
        Fetches all incidents for a specific station.
        This fixes the AttributeError you were seeing.
        """
        # Calls the repository method we added earlier
        return list(self._repository.get_by_station(station_label))

    def update_incident_status(self, incident_id: str, is_valid: bool, is_solved: bool) -> None:
        """
        Updates the status of an incident (valid/solved).
        """
        self._repository.update_status(incident_id, is_valid, is_solved)
        
    # --- ADD TO MalfunctionService.py ---

    def get_all_incidents(self) -> List[Incident]:
        """Fetches all incidents (Admin only)."""
        return list(self._repository.get_all())