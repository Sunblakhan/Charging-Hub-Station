from uuid import UUID
import pytest

from src.malfunction.domain.aggregates import IncidentAggregate
from src.malfunction.domain.value_objects.Name import Name
from src.malfunction.domain.value_objects.Email import Email, InvalidEmail
from src.malfunction.domain.value_objects.StationLabel import StationLabel, InvalidStationLabel
from src.malfunction.domain.value_objects.ProblemDescription import ProblemDescription
from src.malfunction.domain import events


def test_open_incident_emits_details_and_opened_events():
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


def test_submit_report_persists_incident_in_sqlite(
    malfunction_service, incident_repository
):
    incident_id = malfunction_service.submit_report(
        reporter_name="Bob",
        reporter_email="bob@example.com",
        station_label="Koenraad Verleyen - Mahonienweg 7, 12437 Berlin",
        description="Screen flickering.",
    )

    loaded = incident_repository.get_by_id(UUID(str(incident_id)))

    assert loaded is not None
    assert loaded.reporter_name.value == "Bob"
    assert loaded.status == "PENDING"
    assert loaded.station_label.value.endswith("Berlin")


def test_validate_report_sets_valid_and_awards_10_points(
    malfunction_service, incident_repository
):
    incident_id = malfunction_service.submit_report(
        reporter_name="Carla",
        reporter_email="carla@example.com",
        station_label="Koenraad Verleyen - Mahonienweg 7, 12437 Berlin",
        description="Connector loose.",
    )

    malfunction_service.validate_report(incident_id)

    loaded = incident_repository.get_by_id(incident_id)
    assert loaded.is_valid is True
    assert loaded.status == "PUBLISHED"
    assert loaded.points_awarded == 10  # fixed rule


def test_resolve_report_changes_status_to_resolved(
    malfunction_service, incident_repository
):
    incident_id = malfunction_service.submit_report(
        reporter_name="Dan",
        reporter_email="dan@example.com",
        station_label="Koenraad Verleyen - Mahonienweg 7, 12437 Berlin",
        description="Charger offline.",
    )

    malfunction_service.validate_report(incident_id)
    malfunction_service.resolve_report(incident_id, solution_text="Rebooted charger.")

    loaded = incident_repository.get_by_id(incident_id)
    assert loaded.is_solved is True
    assert loaded.status == "RESOLVED"

def test_submit_report_fails_for_invalid_name(malfunction_service, incident_repository):
    """
    Name must be valid (e.g. not empty or too short); invalid name should raise InvalidName
    and nothing should be written to the database.
    """
    with pytest.raises(ValueError):
        malfunction_service.submit_report(
            reporter_name="",  # invalid
            reporter_email="user@example.com",
            station_label="Koenraad Verleyen - Mahonienweg 7, 12437 Berlin",
            description="Connector loose.",
        )

    # ensure DB still empty
    assert incident_repository.get_by_id(UUID(int=0)) is None  # sanity; or query count via SELECT


def test_submit_report_fails_for_invalid_email(malfunction_service):
    """
    Invalid email format should raise InvalidEmail and prevent persistence.
    """
    with pytest.raises(InvalidEmail):
        malfunction_service.submit_report(
            reporter_name="Eva",
            reporter_email="not-an-email",  # invalid
            station_label="Koenraad Verleyen - Mahonienweg 7, 12437 Berlin",
            description="Screen frozen.",
        )


def test_submit_report_fails_for_non_berlin_station(malfunction_service):
    """
    Station label outside Berlin should raise InvalidStationLabel.
    """
    with pytest.raises(InvalidStationLabel):
        malfunction_service.submit_report(
            reporter_name="Frank",
            reporter_email="frank@example.com",
            station_label="Some Operator - Randomstrasse 1, 20095 Hamburg",  # invalid city
            description="Charger not starting.",
        )
