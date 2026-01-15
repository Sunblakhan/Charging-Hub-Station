import pytest

from src.malfunction.domain.value_objects.Name import Name
from src.malfunction.domain.value_objects.Email import Email, InvalidEmail
from src.malfunction.domain.value_objects.StationLabel import (
    StationLabel,
    InvalidStationLabel,
)
from src.malfunction.domain.value_objects.ProblemDescription import (
    ProblemDescription,
    InvalidProblemDescription,
)


# ===================== NAME VALUE OBJECT =====================

def test_name_valid_and_trimmed():
    """Name should trim whitespace."""
    n = Name("  Alice  ")
    assert n.value == "Alice"


@pytest.mark.parametrize("raw", ["", " ", "A"])
def test_name_invalid(raw):
    """Empty, whitespace-only, or too short names should raise ValueError."""
    with pytest.raises(ValueError):
        Name(raw)


def test_name_too_long():
    """Name exceeding 100 chars should raise ValueError."""
    with pytest.raises(ValueError, match="too long"):
        Name("A" * 101)


def test_name_max_length_boundary():
    """Name at exactly 100 chars should be valid."""
    max_name = "A" * 100
    n = Name(max_name)
    assert n.value == max_name
    assert len(n.value) == 100


@pytest.mark.parametrize("spaces_variant", [
    "   Alice   ",
    "\t\tAlice\t\t",
    "\nAlice\n",
])
def test_name_various_whitespace_trimmed(spaces_variant):
    """Name should strip all leading/trailing whitespace."""
    n = Name(spaces_variant)
    assert n.value == "Alice"


# ===================== EMAIL VALUE OBJECT =====================

def test_email_accepts_valid_address():
    """Email should normalize to lowercase."""
    email = Email("User.Example@Example.com")
    assert email.value == "user.example@example.com"


@pytest.mark.parametrize("raw", ["no-at", "user@", "@domain.com", "a b@c.de", "user@@test.com"])
def test_email_rejects_invalid_address(raw):
    """Invalid email formats should raise InvalidEmail."""
    with pytest.raises(InvalidEmail):
        Email(raw)


@pytest.mark.parametrize("email_with_spaces", [
    "  user@test.com  ",
    "\tuser@test.com\t",
])
def test_email_trims_whitespace(email_with_spaces):
    """Email should trim whitespace and normalize."""
    e = Email(email_with_spaces)
    assert e.value == "user@test.com"


def test_email_case_normalization():
    """Email should be lowercase."""
    e1 = Email("User@Test.COM")
    assert e1.value == "user@test.com"


# ===================== STATION LABEL VALUE OBJECT =====================

def test_station_label_accepts_berlin_address():
    """Station label with Berlin should be valid."""
    label = StationLabel("Koenraad Verleyen - Mahonienweg 7, 12437 Berlin")
    assert "Berlin" in label.value


def test_station_label_rejects_non_berlin():
    """Station label without Berlin should raise InvalidStationLabel."""
    with pytest.raises(InvalidStationLabel, match="Berlin"):
        StationLabel("Somewhere Else 1, 12345 Hamburg")


@pytest.mark.parametrize("berlin_variant", [
    "Station - Address 1, 12345 BERLIN",  # uppercase
    "Station - Address 2, 12345 berlin",  # lowercase
    "Station - Address 3, 12345 BerLin",  # mixed case
])
def test_station_label_berlin_case_insensitive(berlin_variant):
    """Berlin check should be case-insensitive."""
    label = StationLabel(berlin_variant)
    assert label.value == berlin_variant.strip()


def test_station_label_requires_comma():
    """Station label must contain comma (full address format)."""
    with pytest.raises(InvalidStationLabel, match="address"):
        StationLabel("Berlin Station without comma")


def test_station_label_whitespace_trimmed():
    """Station label should trim whitespace."""
    label = StationLabel("  Station - Address, 12345 Berlin  ")
    assert label.value == "Station - Address, 12345 Berlin"


def test_station_label_empty_rejected():
    """Empty station label should be rejected."""
    with pytest.raises(InvalidStationLabel):
        StationLabel("")


# ===================== PROBLEM DESCRIPTION VALUE OBJECT =====================

def test_problem_description_must_not_be_empty():
    """Empty description should raise InvalidProblemDescription."""
    with pytest.raises(InvalidProblemDescription):
        ProblemDescription("   ")


def test_problem_description_accepts_text():
    """Valid description should be accepted."""
    desc = ProblemDescription("Charger not working, screen is black.")
    assert "Charger" in desc.value


def test_problem_description_trims_whitespace():
    """Description should trim whitespace."""
    desc = ProblemDescription("  Cable broken  ")
    assert desc.value == "Cable broken"


def test_problem_description_too_long():
    """Description exceeding 2000 chars should raise InvalidProblemDescription."""
    long_desc = "word " * 500  # ~2500 chars
    with pytest.raises(InvalidProblemDescription, match="too long"):
        ProblemDescription(long_desc)


def test_problem_description_max_length_boundary():
    """Description at exactly 2000 chars should be valid."""
    max_desc = "A" * 2000
    desc = ProblemDescription(max_desc)
    assert desc.value == max_desc
    assert len(desc.value) == 2000


@pytest.mark.parametrize("whitespace_desc", [
    "",
    "   ",
    "\t\t",
    "\n\n",
])
def test_problem_description_whitespace_only_rejected(whitespace_desc):
    """Whitespace-only descriptions should be rejected."""
    with pytest.raises(InvalidProblemDescription):
        ProblemDescription(whitespace_desc)
