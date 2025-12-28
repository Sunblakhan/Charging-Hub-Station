import pytest

from src.rating.application.services.RatingService import (
    RatingService,
    StationNotInBerlinError,
)


def test_create_rating_happy_path(rating_repo, station_lookup):
    service = RatingService(rating_repo, station_lookup)

    result = service.create_rating(
        user_name="Alice",
        user_email="alice@example.com",
        station_label="TotalEnergies Charging Solutions - Storkower Str. 175, 1036 Berlin",
        stars=4,
        review_text="good charger",
    )

    assert result["user_name"] == "Alice"
    assert result["stars"] == 4
    assert 1 <= result["average_stars"] <= 5

    # Check DB row exists
    cur = rating_repo._conn.cursor()  # only in tests
    cur.execute(
        "SELECT name, email, station_label, stars, review_text FROM ratings"
    )
    row = cur.fetchone()
    assert row == (
        "Alice",
        "alice@example.com",
        "TotalEnergies Charging Solutions - Storkower Str. 175, 1036 Berlin",
        4,
        "good charger",
    )

def test_station_must_be_in_berlin(rating_repo):
    # Fake lookup that returns False for everything
    class RejectAllLookup:
        def is_station_in_berlin(self, station_label: str) -> bool:
            return False

    service = RatingService(rating_repo, RejectAllLookup())

    with pytest.raises(StationNotInBerlinError):
        service.create_rating(
            user_name="Bob",
            user_email="bob@example.com",
            station_label="Albwerk GmbH & Co. KG - Ennabeurer Weg 0, 72535 Heroldstatt",
            stars=5,
            review_text=None,
        )

def test_create_rating_invalid_email_does_not_persist(rating_repo, station_lookup):
    service = RatingService(rating_repo, station_lookup)

    with pytest.raises(ValueError):
        service.create_rating(
            user_name="Alice",
            user_email="not-an-email",
            station_label="TotalEnergies Charging Solutions - Storkower Str. 175, 1036 Berlin",
            stars=4,
            review_text="ok",
        )

    # DB must still be empty
    cur = rating_repo._conn.cursor()
    cur.execute("SELECT COUNT(*) FROM ratings")
    count = cur.fetchone()[0]
    assert count == 0

def test_create_rating_empty_name_does_not_persist(rating_repo, station_lookup):
    service = RatingService(rating_repo, station_lookup)

    with pytest.raises(ValueError):
        service.create_rating(
            user_name="  ",
            user_email="user@example.com",
            station_label="TotalEnergies Charging Solutions - Storkower Str. 175, 1036 Berlin",
            stars=4,
            review_text="ok",
        )

    cur = rating_repo._conn.cursor()
    cur.execute("SELECT COUNT(*) FROM ratings")
    assert cur.fetchone()[0] == 0


@pytest.mark.parametrize("bad_stars", [0, 6])
def test_create_rating_invalid_stars_does_not_persist(rating_repo, station_lookup, bad_stars):
    service = RatingService(rating_repo, station_lookup)

    with pytest.raises(ValueError):
        service.create_rating(
            user_name="Alice",
            user_email="alice@example.com",
            station_label="TotalEnergies Charging Solutions - Storkower Str. 175, 1036 Berlin",
            stars=bad_stars,
            review_text="ok",
        )

    cur = rating_repo._conn.cursor()
    cur.execute("SELECT COUNT(*) FROM ratings")
    assert cur.fetchone()[0] == 0
