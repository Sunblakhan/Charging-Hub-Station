from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.rating.domain.value_objects.UserId import UserId
from src.rating.domain.value_objects.Name import Name
from src.rating.domain.value_objects.Email import Email
from src.rating.domain.value_objects.StationLabel import StationLabel
from src.rating.domain.value_objects.StarRating import StarRating
from src.rating.domain.value_objects.ReviewText import ReviewText


@dataclass
class Rating:
    rating_id: str
    user_id: UserId
    name: Name
    email: Email
    station_label: StationLabel
    stars: StarRating
    review: ReviewText
    created_at: datetime

    @staticmethod
    def from_primitives(
        rating_id: str,
        user_id: str,
        name: str,
        email: str,
        station_label: str,
        stars: int,
        review_text: Optional[str],
        created_at: datetime,
    ) -> "Rating":
        """
        Factory used when loading from SQLite.
        """
        return Rating(
            rating_id=rating_id,
            user_id=UserId(user_id),
            name=Name(name),
            email=Email(email),
            station_label=StationLabel(station_label),
            stars=StarRating(stars),
            review=ReviewText(review_text),
            created_at=created_at,
        )
