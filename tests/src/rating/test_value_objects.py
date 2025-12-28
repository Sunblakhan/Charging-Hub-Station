import pytest

from src.rating.domain.value_objects.Name import Name
from src.rating.domain.value_objects.Email import Email
from src.rating.domain.value_objects.StarRating import StarRating
from src.rating.domain.value_objects.StationLabel import StationLabel
from src.rating.domain.value_objects.ReviewText import ReviewText


def test_name_valid_and_trimmed():
    n = Name("  Alice  ")
    assert n.value == "Alice"


@pytest.mark.parametrize("raw", ["", " ", "A"])
def test_name_invalid(raw):
    with pytest.raises(ValueError):
        Name(raw)


def test_email_valid():
    e = Email("user@test.com")
    assert e.value == "user@test.com"


@pytest.mark.parametrize("addr", ["user@", "user", "user@x", "user@@test.com"])
def test_email_invalid(addr):
    with pytest.raises(ValueError):
        Email(addr)


@pytest.mark.parametrize("v", [1, 3, 5])
def test_star_valid(v):
    assert StarRating(v).value == v


@pytest.mark.parametrize("v", [0, 6, -1])
def test_star_invalid(v):
    with pytest.raises(ValueError):
        StarRating(v)


def test_station_label_not_empty():
    StationLabel("Some Station, Berlin")
    with pytest.raises(ValueError):
        StationLabel("")


def test_review_text_optional_and_trimmed():
    assert ReviewText(None).value is None
    assert ReviewText("  ").value is None
    assert ReviewText("  nice  ").value == "nice"
