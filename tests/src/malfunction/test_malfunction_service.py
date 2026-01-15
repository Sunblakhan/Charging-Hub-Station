"""
Integration tests for MalfunctionService - Application layer with database.

These tests verify:
- Service orchestration (submit → validate → resolve workflow)
- Database persistence via repository
- Value object invariant enforcement at service boundary
- Business rules (10-point award, Berlin-only stations)
- Edge cases (whitespace trimming, email normalization)
- Repository query methods
"""

from uuid import UUID
import pytest

from src.malfunction.domain.value_objects.Email import InvalidEmail
from src.malfunction.domain.value_objects.StationLabel import InvalidStationLabel
from src.malfunction.domain.value_objects.ProblemDescription import InvalidProblemDescription


# ===================== HAPPY PATH =====================

def test_submit_report_persists_incident_in_sqlite(
    malfunction_service, incident_repository
):
    """SERVICE: Submit should persist incident to database."""
    result = malfunction_service.submit_report(
        reporter_name="Bob",
        reporter_email="bob@example.com",
        station_label="Koenraad Verleyen - Mahonienweg 7, 12437 Berlin",
        description="Screen flickering.",
    )

    loaded = incident_repository.get_by_id(UUID(result["incident_id"]))

    assert loaded is not None
    assert loaded.reporter_name.value == "Bob"
    assert loaded.status == "PENDING"
    assert loaded.station_label.value.endswith("Berlin")


def test_validate_report_sets_valid_and_awards_10_points(
    malfunction_service, incident_repository
):
    """SERVICE: Validation should award points and publish."""
    result = malfunction_service.submit_report(
        reporter_name="Carla",
        reporter_email="carla@example.com",
        station_label="Koenraad Verleyen - Mahonienweg 7, 12437 Berlin",
        description="Connector loose.",
    )

    malfunction_service.validate_report(result["incident_id"])

    loaded = incident_repository.get_by_id(UUID(result["incident_id"]))
    assert loaded.is_valid is True
    assert loaded.status == "IN_PROGRESS"
    assert loaded.points_awarded == 10  # fixed rule


def test_resolve_report_changes_status_to_resolved(
    malfunction_service, incident_repository
):
    """SERVICE: Resolution should mark incident as solved."""
    result = malfunction_service.submit_report(
        reporter_name="Dan",
        reporter_email="dan@example.com",
        station_label="Koenraad Verleyen - Mahonienweg 7, 12437 Berlin",
        description="Charger offline.",
    )

    incident_id = result["incident_id"]
    malfunction_service.validate_report(incident_id)
    malfunction_service.resolve_report(incident_id, solution_text="Rebooted charger.")

    loaded = incident_repository.get_by_id(UUID(incident_id))
    assert loaded.is_solved is True
    assert loaded.status == "SOLVED"


# ===================== ERROR SCENARIOS =====================

def test_submit_report_fails_for_invalid_name(malfunction_service, incident_repository):
    """VALUE OBJECT INVARIANT: Name must be valid (not empty or too short)."""
    with pytest.raises(ValueError):
        malfunction_service.submit_report(
            reporter_name="",  # invalid
            reporter_email="user@example.com",
            station_label="Koenraad Verleyen - Mahonienweg 7, 12437 Berlin",
            description="Connector loose.",
        )

    # Verify no persistence occurred
    all_incidents = list(incident_repository.get_all())
    assert len(all_incidents) == 0


def test_submit_report_fails_for_invalid_email(malfunction_service):
    """VALUE OBJECT INVARIANT: Email format must be valid."""
    with pytest.raises(InvalidEmail):
        malfunction_service.submit_report(
            reporter_name="Eva",
            reporter_email="not-an-email",  # invalid
            station_label="Koenraad Verleyen - Mahonienweg 7, 12437 Berlin",
            description="Screen frozen.",
        )


def test_submit_report_fails_for_non_berlin_station(malfunction_service):
    """DOMAIN RULE: Station must be in Berlin."""
    with pytest.raises(InvalidStationLabel):
        malfunction_service.submit_report(
            reporter_name="Frank",
            reporter_email="frank@example.com",
            station_label="Some Operator - Randomstrasse 1, 20095 Hamburg",  # invalid city
            description="Charger not starting.",
        )


def test_submit_report_fails_for_empty_description(malfunction_service):
    """VALUE OBJECT INVARIANT: Description cannot be empty."""
    with pytest.raises(InvalidProblemDescription):
        malfunction_service.submit_report(
            reporter_name="Grace",
            reporter_email="grace@example.com",
            station_label="Koenraad Verleyen - Mahonienweg 7, 12437 Berlin",
            description="   ",  # whitespace only
        )


def test_submit_report_fails_for_too_long_description(malfunction_service):
    """VALUE OBJECT INVARIANT: Description must not exceed 2000 chars."""
    long_desc = "word " * 500  # ~2500 chars
    with pytest.raises(InvalidProblemDescription, match="too long"):
        malfunction_service.submit_report(
            reporter_name="Henry",
            reporter_email="henry@example.com",
            station_label="Koenraad Verleyen - Mahonienweg 7, 12437 Berlin",
            description=long_desc,
        )


# ===================== EDGE CASES =====================

def test_submit_report_with_whitespace_in_name(malfunction_service, incident_repository):
    """EDGE CASE: Name with whitespace should be trimmed."""
    result = malfunction_service.submit_report(
        reporter_name="  Iris  ",
        reporter_email="iris@example.com",
        station_label="Koenraad Verleyen - Mahonienweg 7, 12437 Berlin",
        description="Charger offline.",
    )

    loaded = incident_repository.get_by_id(UUID(result["incident_id"]))
    assert loaded.reporter_name.value == "Iris"


def test_submit_report_email_normalized_to_lowercase(malfunction_service, incident_repository):
    """EDGE CASE: Email should be normalized to lowercase."""
    result = malfunction_service.submit_report(
        reporter_name="Jack",
        reporter_email="Jack@Example.COM",
        station_label="Koenraad Verleyen - Mahonienweg 7, 12437 Berlin",
        description="Screen flickering.",
    )

    loaded = incident_repository.get_by_id(UUID(result["incident_id"]))
    assert loaded.reporter_email.value == "jack@example.com"


def test_submit_report_station_label_trimmed(malfunction_service, incident_repository):
    """EDGE CASE: Station label should be trimmed."""
    result = malfunction_service.submit_report(
        reporter_name="Kate",
        reporter_email="kate@example.com",
        station_label="  Koenraad Verleyen - Mahonienweg 7, 12437 Berlin  ",
        description="Cable broken.",
    )

    loaded = incident_repository.get_by_id(UUID(result["incident_id"]))
    assert loaded.station_label.value == "Koenraad Verleyen - Mahonienweg 7, 12437 Berlin"


def test_submit_report_description_trimmed(malfunction_service, incident_repository):
    """EDGE CASE: Description should be trimmed."""
    result = malfunction_service.submit_report(
        reporter_name="Leo",
        reporter_email="leo@example.com",
        station_label="Koenraad Verleyen - Mahonienweg 7, 12437 Berlin",
        description="  Charger offline  ",
    )

    loaded = incident_repository.get_by_id(UUID(result["incident_id"]))
    assert loaded.description.value == "Charger offline"


# ===================== BUSINESS LOGIC =====================

def test_validate_report_awards_exactly_10_points(malfunction_service, incident_repository):
    """BUSINESS RULE: Validation always awards 10 points."""
    result = malfunction_service.submit_report(
        reporter_name="Maria",
        reporter_email="maria@example.com",
        station_label="Koenraad Verleyen - Mahonienweg 7, 12437 Berlin",
        description="Connector loose.",
    )

    incident_id = result["incident_id"]
    malfunction_service.validate_report(incident_id)

    loaded = incident_repository.get_by_id(UUID(incident_id))
    assert loaded.points_awarded == 10


def test_validate_report_changes_status_to_published(malfunction_service, incident_repository):
    """BUSINESS RULE: Validation changes status from PENDING to IN_PROGRESS."""
    result = malfunction_service.submit_report(
        reporter_name="Nina",
        reporter_email="nina@example.com",
        station_label="Koenraad Verleyen - Mahonienweg 7, 12437 Berlin",
        description="Screen frozen.",
    )

    incident_id = result["incident_id"]
    loaded_before = incident_repository.get_by_id(UUID(incident_id))
    assert loaded_before.status == "PENDING"

    malfunction_service.validate_report(incident_id)

    loaded_after = incident_repository.get_by_id(UUID(incident_id))
    assert loaded_after.status == "IN_PROGRESS"


def test_resolve_report_changes_status_to_resolved(malfunction_service, incident_repository):
    """BUSINESS RULE: Resolution changes status to SOLVED."""
    result = malfunction_service.submit_report(
        reporter_name="Oscar",
        reporter_email="oscar@example.com",
        station_label="Koenraad Verleyen - Mahonienweg 7, 12437 Berlin",
        description="Charger offline.",
    )

    incident_id = result["incident_id"]
    malfunction_service.validate_report(incident_id)
    malfunction_service.resolve_report(incident_id, solution_text="Replaced cable.")

    loaded = incident_repository.get_by_id(UUID(incident_id))
    assert loaded.status == "SOLVED"
    assert loaded.is_solved is True


# ===================== REPOSITORY QUERY METHODS =====================

def test_repository_get_by_station(malfunction_service, incident_repository):
    """REPOSITORY: Should retrieve all incidents for a specific station."""
    station_label = "Koenraad Verleyen - Mahonienweg 7, 12437 Berlin"

    # Create 3 incidents for the same station
    for i, name in enumerate(["Sam", "Tara", "Uma"]):
        malfunction_service.submit_report(
            reporter_name=name,
            reporter_email=f"{name.lower()}@example.com",
            station_label=station_label,
            description=f"Problem {i+1}",
        )

    # Create 1 incident for a different station
    malfunction_service.submit_report(
        reporter_name="Victor",
        reporter_email="victor@example.com",
        station_label="Different Operator - Street 1, 10115 Berlin",
        description="Problem X",
    )

    incidents_for_station = incident_repository.get_by_station(station_label)
    assert len(incidents_for_station) == 3
    assert all(inc.station_label.value == station_label for inc in incidents_for_station)


def test_repository_get_all(malfunction_service, incident_repository):
    """REPOSITORY: Should retrieve all incidents."""
    # Create 3 incidents
    for i, name in enumerate(["Wendy", "Xander", "Yara"]):
        malfunction_service.submit_report(
            reporter_name=name,
            reporter_email=f"{name.lower()}@example.com",
            station_label="Koenraad Verleyen - Mahonienweg 7, 12437 Berlin",
            description=f"Problem {i+1}",
        )

    all_incidents = list(incident_repository.get_all())
    assert len(all_incidents) == 3


# ===================== ADMIN PANEL: VALIDATION RULES =====================

def test_cannot_mark_solved_without_validating_first(malfunction_service, incident_repository):
    """SERVICE: Business rule - must validate before marking solved."""
    # 1. Submit a report (initially not valid, not solved)
    result = malfunction_service.submit_report(
        reporter_name="Charlie",
        reporter_email="charlie@example.com",
        station_label="Koenraad Verleyen - Mahonienweg 7, 12437 Berlin",
        description="Charging stopped mid-session.",
    )
    incident_id = result["incident_id"]
    
    # 2. Try to mark as solved WITHOUT validating first -> Should raise error
    with pytest.raises(ValueError, match="Cannot mark as solved without validating"):
        malfunction_service.update_incident_status(
            incident_id=incident_id,
            is_valid=False,
            is_solved=True
        )
    
    # 3. Verify incident is still PENDING
    loaded = incident_repository.get_by_id(UUID(incident_id))
    assert loaded.status == "PENDING"
    assert not loaded.is_valid
    assert not loaded.is_solved


def test_can_mark_solved_after_validating(malfunction_service, incident_repository):
    """SERVICE: After validating, can mark as solved."""
    # 1. Submit report
    result = malfunction_service.submit_report(
        reporter_name="Diana",
        reporter_email="diana@example.com",
        station_label="Koenraad Verleyen - Mahonienweg 7, 12437 Berlin",
        description="Overcurrent protection tripped.",
    )
    incident_id = result["incident_id"]
    
    # 2. Validate first
    malfunction_service.update_incident_status(
        incident_id=incident_id,
        is_valid=True,
        is_solved=False
    )
    
    loaded = incident_repository.get_by_id(UUID(incident_id))
    assert loaded.is_valid
    assert not loaded.is_solved
    assert loaded.status == "IN_PROGRESS"
    
    # 3. Now can mark as solved
    malfunction_service.update_incident_status(
        incident_id=incident_id,
        is_valid=True,
        is_solved=True
    )
    
    loaded = incident_repository.get_by_id(UUID(incident_id))
    assert loaded.is_valid
    assert loaded.is_solved
    assert loaded.status == "SOLVED"


def test_validate_checkbox_constraint_in_admin_panel(malfunction_service, incident_repository):
    """SERVICE: Admin panel enforces validation -> solved constraint."""
    # Test documents the UI business rule:
    # is_valid checkbox must be checked before is_solved checkbox
    result = malfunction_service.submit_report(
        reporter_name="Emil",
        reporter_email="emil@example.com",
        station_label="Koenraad Verleyen - Mahonienweg 7, 12437 Berlin",
        description="Power supply issue.",
    )
    incident_id = result["incident_id"]
    
    # Cannot directly skip validation and go to solved
    with pytest.raises(ValueError):
        malfunction_service.update_incident_status(
            incident_id=incident_id,
            is_valid=False,
            is_solved=True
        )
    
    # Service enforces the constraint
    loaded = incident_repository.get_by_id(UUID(incident_id))
    assert loaded.status == "PENDING"

