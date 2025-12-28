import sqlite3
import pytest

from src.rating.infrastructure.repositories.SqliteRatingRepository import (
    SqliteRatingRepository,
)


class FakeStationLookup:
    def __init__(self, allowed):
        self.allowed = set(allowed)

    def is_station_in_berlin(self, station_label: str) -> bool:
        return station_label in self.allowed


@pytest.fixture
def sqlite_conn(tmp_path):
    db_file = tmp_path / "ratings.db"
    conn = sqlite3.connect(db_file.as_posix())
    yield conn
    conn.close()


@pytest.fixture
def rating_repo(sqlite_conn):
    return SqliteRatingRepository(sqlite_conn)


@pytest.fixture
def station_lookup():
    return FakeStationLookup(
        {
            "Berliner Stadtwerke KommunalPartner GmbH - Leipziger Platz 19, 1011 Berlin",
            "TotalEnergies Charging Solutions - Storkower Str. 175, 1036 Berlin",
            "Berliner Stadtwerke KommunalPartner GmbH - Uhlandstr. 177, 1062 Berlin",
            "Design Offices GmbH (Köln) - Gartenstraße 87, 10115 Berlin",
            "TotalEnergies Charging Solutions - Ackerstr. 118, 10115 Berlin",
            # add more Berlin stations here
        }
    )
