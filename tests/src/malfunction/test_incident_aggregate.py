"""
Unit tests for IncidentAggregate - Domain layer only, no database.

These tests verify:
- Aggregate creation and event emission
- Domain validation workflow  
- State transitions (PENDING → IN_PROGRESS → SOLVED)
- Event ordering and idempotency
- Aggregate invariants
"""

from src.malfunction.domain import events
from src.malfunction.domain.aggregates import IncidentAggregate
from src.malfunction.domain.value_objects.Email import Email
from src.malfunction.domain.value_objects.Name import Name
from src.malfunction.domain.value_objects.ProblemDescription import ProblemDescription
from src.malfunction.domain.value_objects.StationLabel import StationLabel


# ===================== HAPPY PATH =====================

def test_open_incident_emits_details_and_opened_events():
    """AGGREGATE: Creating incident should emit opening events."""
    aggregate = IncidentAggregate.open(
        reporter_name=Name("Alice"),
        reporter_email=Email("alice@example.com"),
        station_label=StationLabel(
            "Koenraad Verleyen - Mahonienweg 7, 12437 Berlin"
        ),
        description=ProblemDescription("Cable broken."),
    )

    assert aggregate.incident.status == "PENDING"
    assert not aggregate.incident.is_valid
    assert not aggregate.incident.is_solved

    types = {type(e) for e in aggregate.domain_events}
    assert events.DetailsEntered in types
    assert events.MalfunctionReportOpened in types


# ===================== VALIDATION WORKFLOW =====================

def test_aggregate_validate_report_emits_events():
    """AGGREGATE: Validation should emit multiple domain events."""
    aggregate = IncidentAggregate.open(
        reporter_name=Name("Paula"),
        reporter_email=Email("paula@example.com"),
        station_label=StationLabel("Koenraad Verleyen - Mahonienweg 7, 12437 Berlin"),
        description=ProblemDescription("Cable broken."),
    )

    # Clear initial events
    initial_event_count = len(aggregate.domain_events)
    
    aggregate.validate_report(points_for_report=10)

    # Verify validation emitted new events
    validation_events = aggregate.domain_events[initial_event_count:]
    event_types = {type(e) for e in validation_events}

    assert events.ReportValidatedAndSubmitted in event_types
    assert events.PointsAwardedToReporter in event_types
    assert events.ReportNotifiedToAdminAndOperator in event_types
    assert events.WarningDisplayedToAllUsers in event_types
    assert events.ReportPublishedToUsers in event_types
    assert events.IssuesStatusUpdateReport in event_types


def test_aggregate_resolve_emits_solution_event():
    """AGGREGATE: Resolution should emit solution event."""
    aggregate = IncidentAggregate.open(
        reporter_name=Name("Quinn"),
        reporter_email=Email("quinn@example.com"),
        station_label=StationLabel("Koenraad Verleyen - Mahonienweg 7, 12437 Berlin"),
        description=ProblemDescription("Screen flickering."),
    )

    aggregate.validate_report(points_for_report=10)
    initial_event_count = len(aggregate.domain_events)

    aggregate.resolve(solution_text="Rebooted system.")

    resolution_events = aggregate.domain_events[initial_event_count:]
    event_types = {type(e) for e in resolution_events}

    assert events.SolutionProvided in event_types
    assert events.IssuesStatusUpdateReport in event_types


# ===================== STATE TRANSITIONS =====================

def test_aggregate_status_transitions_pending_to_published_to_resolved():
    """AGGREGATE: Status should transition correctly through workflow."""
    aggregate = IncidentAggregate.open(
        reporter_name=Name("Rachel"),
        reporter_email=Email("rachel@example.com"),
        station_label=StationLabel("Koenraad Verleyen - Mahonienweg 7, 12437 Berlin"),
        description=ProblemDescription("Connector loose."),
    )

    # Initial state
    assert aggregate.incident.status == "PENDING"
    assert not aggregate.incident.is_valid
    assert not aggregate.incident.is_solved

    # After validation
    aggregate.validate_report(points_for_report=10)
    assert aggregate.incident.status == "IN_PROGRESS"
    assert aggregate.incident.is_valid
    assert not aggregate.incident.is_solved

    # After resolution
    aggregate.resolve(solution_text="Replaced connector.")
    assert aggregate.incident.status == "SOLVED"
    assert aggregate.incident.is_valid
    assert aggregate.incident.is_solved


# ===================== IDEMPOTENCY =====================

def test_aggregate_validate_twice_is_idempotent():
    """AGGREGATE: Validating twice should not award points twice."""
    aggregate = IncidentAggregate.open(
        reporter_name=Name("Zara"),
        reporter_email=Email("zara@example.com"),
        station_label=StationLabel("Koenraad Verleyen - Mahonienweg 7, 12437 Berlin"),
        description=ProblemDescription("Screen frozen."),
    )

    aggregate.validate_report(points_for_report=10)
    assert aggregate.incident.points_awarded == 10

    # Validate again
    aggregate.validate_report(points_for_report=10)
    # Should still be 10, not 20
    assert aggregate.incident.points_awarded == 10


def test_aggregate_resolve_twice_is_idempotent():
    """AGGREGATE: Resolving twice should not change state."""
    aggregate = IncidentAggregate.open(
        reporter_name=Name("Adam"),
        reporter_email=Email("adam@example.com"),
        station_label=StationLabel("Koenraad Verleyen - Mahonienweg 7, 12437 Berlin"),
        description=ProblemDescription("Charger offline."),
    )

    aggregate.validate_report(points_for_report=10)
    aggregate.resolve(solution_text="Fixed issue.")

    event_count_after_first_resolve = len(aggregate.domain_events)

    # Resolve again
    aggregate.resolve(solution_text="Fixed issue again.")

    # Should not emit new events
    assert len(aggregate.domain_events) == event_count_after_first_resolve
