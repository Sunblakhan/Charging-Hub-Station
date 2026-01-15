from uuid import UUID
from typing import List, Dict, Any

from src.malfunction.domain.aggregates.IncidentAggregate import IncidentAggregate
from src.malfunction.infrastructure.repositories.IncidentRepository import IncidentRepository
from src.malfunction.domain.value_objects.Name import Name
from src.malfunction.domain.value_objects.Email import Email
from src.malfunction.domain.value_objects.StationLabel import StationLabel
from src.malfunction.domain.value_objects.ProblemDescription import ProblemDescription


class MalfunctionService:
    """
    Application service for malfunction reporting use cases.
    Orchestrates workflow using IncidentAggregate.
    """
    
    def __init__(self, repository: IncidentRepository):
        self._repository = repository

    def submit_report(
        self,
        reporter_name: str,
        reporter_email: str,
        station_label: str,
        description: str,
        is_valid: bool = False,
    ) -> Dict[str, Any]:
        """
        Creates a new malfunction report and persists it.
        Returns DTO with incident ID only (as per UI requirement).
        
        Args:
            reporter_name: Name of reporter
            reporter_email: Email of reporter
            station_label: Station where issue occurred
            description: Problem description
            is_valid: Whether to auto-validate (True for operators, False for public)
        
        Returns:
            Dict with incident_id key
        """
        # 1. Create aggregate (emits opening events)
        agg = IncidentAggregate.open(
            reporter_name=Name(reporter_name),
            reporter_email=Email(reporter_email),
            station_label=StationLabel(station_label),
            description=ProblemDescription(description),
        )
        
        # 2. Auto-validate if operator submitted
        if is_valid:
            agg.validate_report(points_for_report=10)
        
        # 3. Persist incident
        self._repository.save(agg.incident)
        
        # 4. Return minimal DTO (only incident ID as per UI requirement)
        return {
            "incident_id": str(agg.incident.id),
        }

    def validate_report(self, incident_id: str) -> None:
        """
        Admin validates a malfunction report.
        Awards 10 points and publishes to users.
        """
        # 1. Load incident from repository
        incident = self._repository.get_by_id(UUID(incident_id))
        if not incident:
            raise ValueError(f"Incident not found: {incident_id}")
        
        # 2. Reconstitute aggregate
        agg = IncidentAggregate(incident=incident, domain_events=[])
        
        # 3. Apply domain logic (emits validation events)
        agg.validate_report(points_for_report=10)
        
        # 4. Persist updated state
        self._repository.save(agg.incident)

    def resolve_report(self, incident_id: str, solution_text: str) -> None:
        """
        Operator resolves a malfunction with solution details.
        """
        # 1. Load incident
        incident = self._repository.get_by_id(UUID(incident_id))
        if not incident:
            raise ValueError(f"Incident not found: {incident_id}")
        
        # 2. Reconstitute aggregate
        agg = IncidentAggregate(incident=incident, domain_events=[])
        
        # 3. Apply resolution (emits solution events)
        agg.resolve(solution_text=solution_text)
        
        # 4. Persist
        self._repository.save(agg.incident)

    def update_incident_status(self, incident_id: str, is_valid: bool, is_solved: bool) -> None:
        """
        Admin updates incident validation and solved status.
        
        Business Rule: Can only mark as solved if marked as valid.
        
        Args:
            incident_id: ID of incident to update
            is_valid: Whether the report is valid
            is_solved: Whether the issue is solved
            
        Raises:
            ValueError: If trying to mark solved without marking valid
        """
        # 1. Load incident
        incident = self._repository.get_by_id(UUID(incident_id))
        if not incident:
            raise ValueError(f"Incident not found: {incident_id}")
        
        # 2. Business Rule: Cannot solve without validating
        if is_solved and not is_valid:
            raise ValueError("Cannot mark as solved without validating the report first")
        
        # 3. Update state
        incident.is_valid = is_valid
        incident.is_solved = is_solved
        
        # 5. Update status based on state
        if is_solved:
            incident.status = "SOLVED"
        elif is_valid:
            incident.status = "IN_PROGRESS"
        else:
            incident.status = "PENDING"
        
        # 6. Persist
        self._repository.save(incident)

    def get_incidents_for_station(self, station_label: str) -> List:
        """Query method - returns list of incidents for a station."""
        return list(self._repository.get_by_station(station_label))

    def get_all_incidents(self) -> List:
        """Query method - returns all incidents (for admin view)."""
        return list(self._repository.get_all())