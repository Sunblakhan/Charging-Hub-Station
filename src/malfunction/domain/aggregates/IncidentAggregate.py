from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import List

from src.malfunction.domain.entities.Incident import Incident
from src.malfunction.domain import events
from src.malfunction.domain.value_objects.Name import Name



@dataclass
class IncidentAggregate:
    """
    Aggregate root around Incident entity plus domain events.
    """

    incident: Incident
    domain_events: List[object] = field(default_factory=list)

    @classmethod
    def open(
        cls,
        reporter_name: Name,
        reporter_email,
        station_label,
        description,
    ) -> "IncidentAggregate":
        """
        Factory to create a new incident and emit opening events.
        reporter_email, station_label, description are already value objects.
        """
        entity = Incident(
            reporter_name=reporter_name,
            reporter_email=reporter_email,
            station_label=station_label,
            description=description,
        )

        aggregate = cls(incident=entity)

        now = datetime.now(UTC)
        aggregate.domain_events.append(
            events.MalfunctionReportOpened(
                incident_id=entity.id,
                occurred_at=now,
            )
        )
        aggregate.domain_events.append(
            events.DetailsEntered(
                incident_id=entity.id,
                occurred_at=now,
            )
        )

        return aggregate

    def validate_report(self, points_for_report: int = 10) -> None:
        """
        Admin verifies malfunction as valid.
        """
        if self.incident.is_valid:
            return

        old_status = self.incident.status

        self.incident.is_valid = True
        self.incident.status = "IN_PROGRESS"
        self.incident.points_awarded += points_for_report

        now = datetime.now(UTC)

        self.domain_events.append(
            events.ReportValidatedAndSubmitted(
                incident_id=self.incident.id,
                occurred_at=now,
            )
        )
        self.domain_events.append(
            events.PointsAwardedToReporter(
                incident_id=self.incident.id,
                occurred_at=now,
                points=points_for_report,
            )
        )
        self.domain_events.append(
            events.ReportNotifiedToAdminAndOperator(
                incident_id=self.incident.id,
                occurred_at=now,
            )
        )
        self.domain_events.append(
            events.WarningDisplayedToAllUsers(
                incident_id=self.incident.id,
                occurred_at=now,
            )
        )
        self.domain_events.append(
            events.ReportPublishedToUsers(
                incident_id=self.incident.id,
                occurred_at=now,
            )
        )
        self.domain_events.append(
            events.IssuesStatusUpdateReport(
                incident_id=self.incident.id,
                occurred_at=now,
                old_status=old_status,
                new_status=self.incident.status,
            )
        )

    def resolve(self, solution_text: str) -> None:
        """
        Operator/admin resolves the malfunction.
        """
        if self.incident.is_solved:
            return

        old_status = self.incident.status
        self.incident.is_solved = True
        self.incident.status = "SOLVED"

        now = datetime.now(UTC)

        self.domain_events.append(
            events.SolutionProvided(
                incident_id=self.incident.id,
                occurred_at=now,
                solution_text=solution_text,
            )
        )
        self.domain_events.append(
            events.IssuesStatusUpdateReport(
                incident_id=self.incident.id,
                occurred_at=now,
                old_status=old_status,
                new_status=self.incident.status,
            )
        )
