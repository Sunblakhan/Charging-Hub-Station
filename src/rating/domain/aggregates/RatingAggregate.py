# src/rating/domain/aggregates/RatingAggregate.py
from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import List, Optional

from src.rating.domain.entities.Rating import Rating
from src.rating.domain.value_objects.UserId import UserId
from src.rating.domain.value_objects.Name import Name
from src.rating.domain.value_objects.Email import Email
from src.rating.domain.value_objects.StationLabel import StationLabel
from src.rating.domain.value_objects.StarRating import StarRating
from src.rating.domain.value_objects.ReviewText import ReviewText

from src.rating.domain.events.NewRatingCreated import NewRatingCreated
from src.rating.domain.events.RatingSubmitted import RatingSubmitted
from src.rating.domain.events.RatingValidated import RatingValidated
from src.rating.domain.events.RatingStored import RatingStored
from src.rating.domain.events.StationsAvgRatingUpdated import StationsAvgRatingUpdated
from src.rating.domain.events.ReviewPublished import ReviewPublished
from src.rating.domain.events.RatingMadeVisibleToUsers import RatingMadeVisibleToUsers
from src.rating.domain.events.SelectChargingStation import SelectChargingStation


@dataclass
class RatingAggregate:
    rating: Rating
    _events: List[object] = field(default_factory=list, init=False, repr=False)

    @staticmethod
    def create_new(
        rating_id: str,
        user_id: str,
        user_name: str,
        user_email: str,
        station_label: str,
        stars: int,
        review_text: Optional[str] = None,
        created_at: Optional[datetime] = None,
    ) -> "RatingAggregate":
        """
        Factory used when the user fills in the rating form and presses 'submit'.
        Enforces all invariants via value objects and emits NewRatingCreated + RatingSubmitted.
        """
        created_at = created_at or datetime.now(UTC)

        rating_entity = Rating(
            rating_id=rating_id,
            user_id=UserId(user_id),
            name=Name(user_name),
            email=Email(user_email),
            station_label=StationLabel(station_label),
            stars=StarRating(stars),
            review=ReviewText(review_text),
            created_at=created_at,
        )

        agg = RatingAggregate(rating=rating_entity)

        # 1. user selected station & submitted rating
        agg._events.append(
            SelectChargingStation(
                user_id=user_id,
                station_label=station_label,
                selected_at=created_at,
            )
        )
        agg._events.append(
            NewRatingCreated(
                rating_id=rating_id,
                station_label=station_label,
                user_name=user_name,
                user_email=user_email,
                stars=stars,
                review_text=review_text or "",
                occurred_at=created_at,
            )
        )
        agg._events.append(
            RatingSubmitted(
                rating_id=rating_id,
                station_label=station_label,
                submitted_at=created_at,
            )
        )

        return agg

    # ---------- Workflow steps ----------

    def mark_valid(self, is_valid: bool, reason: Optional[str] = None) -> None:
        """
        Called after running domain validation rules (email format, Berlin station etc.).
        Only appends an event; the aggregate state is already valid because of value objects.
        """
        self._events.append(
            RatingValidated(
                rating_id=self.rating.rating_id,
                is_valid=is_valid,
                reason=reason,
                validated_at=datetime.now(UTC),
            )
        )

    def mark_stored(self) -> None:
        """
        Called by application service after writing rating to SQLite.
        """
        self._events.append(
            RatingStored(
                rating_id=self.rating.rating_id,
                station_label=self.rating.station_label.value,
                stored_at=datetime.now(UTC),
            )
        )

    def update_station_average(self, new_average: float) -> None:
        """
        Called by application service after recomputing the station's average rating.
        """
        self._events.append(
            StationsAvgRatingUpdated(
                station_label=self.rating.station_label.value,
                new_average=new_average,
                updated_at=datetime.now(UTC),
            )
        )

    def publish_review(self) -> None:
        """
        Called when the review becomes visible on the station profile.
        """
        now = datetime.now(UTC)
        self._events.append(
            ReviewPublished(
                rating_id=self.rating.rating_id,
                station_label=self.rating.station_label.value,
                visible_from=now,
            )
        )
        self._events.append(
            RatingMadeVisibleToUsers(
                rating_id=self.rating.rating_id,
                station_label=self.rating.station_label.value,
                published_at=now,
            )
        )

    # ---------- Events access ----------

    @property
    def events(self) -> list[object]:
        """
        Returns a copy so tests/application can inspect the domain events.
        """
        return list(self._events)
