import sqlite3
import pytest

from src.malfunction.infrastructure.repositories.IncidentRepository import IncidentRepository
from src.malfunction.application.services.MalfunctionService import MalfunctionService


@pytest.fixture
def sqlite_connection():
    # fresh in-memory SQLite DB per test run
    conn = sqlite3.connect(":memory:")
    yield conn
    conn.close()


@pytest.fixture
def incident_repository(sqlite_connection):
    return IncidentRepository(sqlite_connection)


@pytest.fixture
def malfunction_service(incident_repository):
    return MalfunctionService(incident_repository)
