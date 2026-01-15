# src/rating/application/services/RatingService.py
from typing import Dict, Any

from src.rating.domain.aggregates.RatingAggregate import RatingAggregate
from src.rating.domain.exceptions import DuplicateRatingError, StationNotInBerlinError
from src.rating.infrastructure.repositories.RatingRepositoryInterface import (
    RatingRepositoryInterface,
)
from src.rating.application.services.station_lookup import StationLookupInterface


class RatingService:
    """
    Application service for the 'create rating' use case.
    """

    def __init__(
        self,
        repo: RatingRepositoryInterface,
        station_lookup: StationLookupInterface,
    ) -> None:
        self._repo = repo
        self._station_lookup = station_lookup

    def create_rating(
        self,
        user_name: str,
        user_email: str,
        station_label: str,
        stars: int,
        review_text: str | None,
    ) -> Dict[str, Any]:
        """
        Orchestrates the use case:
        1. Check station is in Berlin.
        2. Build RatingAggregate (emits NewRatingCreated + RatingSubmitted + SelectChargingStation).
        3. Mark rating as valid.
        4. Persist rating in SQLite.
        5. Recalculate and emit StationsAvgRatingUpdated.
        6. Publish review and emit ReviewPublished + RatingMadeVisibleToUsers.
        7. Return a DTO for the UI.
        """
        if not self._station_lookup.is_station_in_berlin(station_label):
            raise StationNotInBerlinError(station_label)

        rating_id = self._repo.next_id()
        user_id = "user-temporary-id"  # replace with real user id logic later

        # 1–3: create and validate aggregate
        agg = RatingAggregate.create_new(
            rating_id=rating_id,
            user_id=user_id,
            user_name=user_name,
            user_email=user_email,
            station_label=station_label,
            stars=stars,
            review_text=review_text,
        )

        if self._repo.exists_for_user_and_station(
            agg.rating.email.value, agg.rating.station_label.value
        ):
            raise DuplicateRatingError(
                user_email=agg.rating.email.value,
                station_label=agg.rating.station_label.value,
            )

        agg.mark_valid(is_valid=True, reason=None)

        # 4: persist rating
        self._repo.save(agg.rating)
        agg.mark_stored()

        # 5: recompute average for this station
        ratings = self._repo.all_for_station(station_label)
        new_avg = sum(r.stars.value for r in ratings) / len(ratings)
        agg.update_station_average(new_avg)

        # 6: mark review as published
        agg.publish_review()

        # 7: build DTO (UI response)
        return {
            "rating_id": agg.rating.rating_id,
            "station_label": agg.rating.station_label.value,
            "user_name": agg.rating.name.value,
            "user_email": agg.rating.email.value,
            "stars": agg.rating.stars.value,
            "review_text": agg.rating.review.value,
            "average_stars": new_avg,
            "events": agg.events,  # handy for tests; UI may ignore
        }
