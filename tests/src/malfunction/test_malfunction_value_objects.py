import pytest

from src.malfunction.domain.value_objects.Email import Email, InvalidEmail
from src.malfunction.domain.value_objects.StationLabel import (
    StationLabel,
    InvalidStationLabel,
)
from src.malfunction.domain.value_objects.ProblemDescription import (
    ProblemDescription,
    InvalidProblemDescription,
)


def test_email_accepts_valid_address():
    email = Email("User.Example@Example.com")
    assert email.value == "user.example@example.com"


@pytest.mark.parametrize("raw", ["no-at", "user@", "@domain.com", "a b@c.de"])
def test_email_rejects_invalid_address(raw):
    with pytest.raises(InvalidEmail):
        Email(raw)


def test_station_label_accepts_berlin_address():
    label = StationLabel("Koenraad Verleyen - Mahonienweg 7, 12437 Berlin")
    assert "Berlin" in label.value


def test_station_label_rejects_non_berlin():
    with pytest.raises(InvalidStationLabel):
        StationLabel("Somewhere Else 1, 12345 Hamburg")


def test_problem_description_must_not_be_empty():
    with pytest.raises(InvalidProblemDescription):
        ProblemDescription("   ")


def test_problem_description_accepts_text():
    desc = ProblemDescription("Charger not working, screen is black.")
    assert "Charger" in desc.value
