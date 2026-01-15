import pytest

from src.rating.application.services.RatingService import (
    RatingService,
    DuplicateRatingError,
    StationNotInBerlinError,
)


# ===================== HAPPY PATH =====================

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


# ===================== ERROR SCENARIOS =====================

def test_station_must_be_in_berlin(rating_repo):
    """DOMAIN RULE: Ratings must be for Berlin stations only."""
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

    # CRITICAL: Verify persistence is blocked (no row inserted)
    cur = rating_repo._conn.cursor()
    cur.execute("SELECT COUNT(*) FROM ratings")
    count = cur.fetchone()[0]
    assert count == 0, "Rating should NOT be persisted for non-Berlin station"


def test_create_rating_invalid_email_does_not_persist(rating_repo, station_lookup):
    """VALUE OBJECT INVARIANT: Email format must be valid."""
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
    """VALUE OBJECT INVARIANT: Name cannot be empty."""
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


@pytest.mark.parametrize("bad_stars", [0, 6, -1, 10])
def test_create_rating_invalid_stars_does_not_persist(rating_repo, station_lookup, bad_stars):
    """VALUE OBJECT INVARIANT: Stars must be 1-5."""
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


# ===================== EDGE CASES =====================

def test_create_rating_with_optional_review_none(rating_repo, station_lookup):
    """EDGE CASE: Review is optional; None should be persisted."""
    service = RatingService(rating_repo, station_lookup)

    result = service.create_rating(
        user_name="Charlie",
        user_email="charlie@example.com",
        station_label="TotalEnergies Charging Solutions - Storkower Str. 175, 1036 Berlin",
        stars=3,
        review_text=None,
    )

    assert result["review_text"] is None

    # Verify DB stores NULL
    cur = rating_repo._conn.cursor()
    cur.execute("SELECT review_text FROM ratings WHERE name = ?", ("Charlie",))
    stored_review = cur.fetchone()[0]
    assert stored_review is None


def test_create_rating_with_whitespace_only_review(rating_repo, station_lookup):
    """EDGE CASE: Whitespace-only review should normalize to None."""
    service = RatingService(rating_repo, station_lookup)

    result = service.create_rating(
        user_name="Diana",
        user_email="diana@example.com",
        station_label="TotalEnergies Charging Solutions - Storkower Str. 175, 1036 Berlin",
        stars=5,
        review_text="   \t\n   ",  # whitespace only
    )

    # ReviewText normalizes whitespace-only to None
    assert result["review_text"] is None

    # Verify DB stores NULL
    cur = rating_repo._conn.cursor()
    cur.execute("SELECT review_text FROM ratings WHERE name = ?", ("Diana",))
    stored_review = cur.fetchone()[0]
    assert stored_review is None


def test_create_rating_name_with_leading_trailing_spaces(rating_repo, station_lookup):
    """EDGE CASE: Name should be trimmed before storage."""
    service = RatingService(rating_repo, station_lookup)

    result = service.create_rating(
        user_name="  Eve  ",
        user_email="eve@example.com",
        station_label="TotalEnergies Charging Solutions - Storkower Str. 175, 1036 Berlin",
        stars=4,
        review_text="good",
    )

    # Name value object should have trimmed it
    assert result["user_name"] == "Eve"

    # Verify DB stores trimmed name
    cur = rating_repo._conn.cursor()
    cur.execute("SELECT name FROM ratings WHERE email = ?", ("eve@example.com",))
    stored_name = cur.fetchone()[0]
    assert stored_name == "Eve"


# ===================== BUSINESS LOGIC =====================

def test_average_calculation_single_rating(rating_repo, station_lookup):
    """BUSINESS LOGIC: Average with single rating equals the rating."""
    service = RatingService(rating_repo, station_lookup)

    result = service.create_rating(
        user_name="Frank",
        user_email="frank@example.com",
        station_label="TotalEnergies Charging Solutions - Storkower Str. 175, 1036 Berlin",
        stars=5,
        review_text="excellent",
    )

    # Single rating: average should be 5.0
    assert result["average_stars"] == 5.0


def test_average_calculation_multiple_ratings(rating_repo, station_lookup):
    """BUSINESS LOGIC: Average should be correctly calculated from multiple ratings."""
    service = RatingService(rating_repo, station_lookup)

    # First rating: 4 stars
    service.create_rating(
        user_name="Grace",
        user_email="grace@example.com",
        station_label="TotalEnergies Charging Solutions - Storkower Str. 175, 1036 Berlin",
        stars=4,
        review_text="good",
    )

    # Second rating: 2 stars (same station)
    result2 = service.create_rating(
        user_name="Henry",
        user_email="henry@example.com",
        station_label="TotalEnergies Charging Solutions - Storkower Str. 175, 1036 Berlin",
        stars=2,
        review_text="poor",
    )

    # Average should be (4 + 2) / 2 = 3.0
    assert result2["average_stars"] == 3.0


def test_multiple_ratings_different_stations(rating_repo, station_lookup):
    """BUSINESS LOGIC: Ratings for different stations should have separate averages."""
    service = RatingService(rating_repo, station_lookup)

    # Rating for Station A: 5 stars
    result1 = service.create_rating(
        user_name="Iris",
        user_email="iris@example.com",
        station_label="TotalEnergies Charging Solutions - Storkower Str. 175, 1036 Berlin",
        stars=5,
        review_text="great",
    )

    # Rating for Station B: 2 stars
    result2 = service.create_rating(
        user_name="Jack",
        user_email="jack@example.com",
        station_label="Berliner Stadtwerke KommunalPartner GmbH - Leipziger Platz 19, 1011 Berlin",
        stars=2,
        review_text="bad",
    )

    # Station A average should still be 5.0 (only 1 rating)
    assert result1["average_stars"] == 5.0
    # Station B average should be 2.0 (only 1 rating)
    assert result2["average_stars"] == 2.0


def test_user_cannot_rate_same_station_twice(rating_repo, station_lookup):
    """BUSINESS RULE: A user must not rate the same station multiple times."""
    service = RatingService(rating_repo, station_lookup)

    service.create_rating(
        user_name="Alice",
        user_email="alice@example.com",
        station_label="TotalEnergies Charging Solutions - Storkower Str. 175, 1036 Berlin",
        stars=4,
        review_text="good",
    )

    with pytest.raises(DuplicateRatingError):
        service.create_rating(
            user_name="Alice",
            user_email="alice@example.com",
            station_label="TotalEnergies Charging Solutions - Storkower Str. 175, 1036 Berlin",
            stars=5,
            review_text="trying again",
        )

    # Only the first rating should be stored
    cur = rating_repo._conn.cursor()
    cur.execute(
        "SELECT stars, review_text FROM ratings WHERE email = ?",
        ("alice@example.com",),
    )
    rows = cur.fetchall()
    assert rows == [(4, "good")]


# ===================== USER IDENTITY =====================

def test_rating_stores_user_email(rating_repo, station_lookup):
    """INVARIANT: User email must be persisted and retrievable."""
    service = RatingService(rating_repo, station_lookup)

    service.create_rating(
        user_name="Kate",
        user_email="kate@example.com",
        station_label="TotalEnergies Charging Solutions - Storkower Str. 175, 1036 Berlin",
        stars=4,
        review_text="ok",
    )

    cur = rating_repo._conn.cursor()
    cur.execute("SELECT email FROM ratings WHERE name = ?", ("Kate",))
    stored_email = cur.fetchone()[0]
    assert stored_email == "kate@example.com"


# ===================== EVENTS =====================

def test_create_rating_emits_events(rating_repo, station_lookup):
    """AGGREGATE: Creating a rating should emit multiple domain events."""
    service = RatingService(rating_repo, station_lookup)

    result = service.create_rating(
        user_name="Leo",
        user_email="leo@example.com",
        station_label="TotalEnergies Charging Solutions - Storkower Str. 175, 1036 Berlin",
        stars=4,
        review_text="great charger",
    )

    events = result["events"]
    event_types = [type(e).__name__ for e in events]

    # Should include all workflow events
    assert "SelectChargingStation" in event_types
    assert "NewRatingCreated" in event_types
    assert "RatingSubmitted" in event_types
    assert "RatingValidated" in event_types
    assert "RatingStored" in event_types
    assert "StationsAvgRatingUpdated" in event_types
    assert "ReviewPublished" in event_types
    assert "RatingMadeVisibleToUsers" in event_types
