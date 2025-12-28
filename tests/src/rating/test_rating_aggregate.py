from src.rating.domain.aggregates.RatingAggregate import RatingAggregate


def test_create_new_emits_basic_events():
    agg = RatingAggregate.create_new(
        rating_id="r1",
        user_id="u1",
        user_name="Alice",
        user_email="alice@example.com",
        station_label="Berliner Stadtwerke KommunalPartner GmbH - Leipziger Platz 19, 1011 Berlin",
        stars=4,
        review_text="good charger",
    )

    ev_types = {type(e).__name__ for e in agg.events}
    assert "SelectChargingStation" in ev_types
    assert "NewRatingCreated" in ev_types
    assert "RatingSubmitted" in ev_types

    new_rating_event = next(
        e for e in agg.events if type(e).__name__ == "NewRatingCreated"
    )
    assert new_rating_event.user_name == "Alice"
    assert new_rating_event.stars == 4

def test_validation_and_publish_events():
    agg = RatingAggregate.create_new(
        rating_id="r2",
        user_id="u2",
        user_name="Bob",
        user_email="bob@example.com",
        station_label="Design Offices GmbH (Köln) - Gartenstraße 87, 10115 Berlin",
        stars=5,
        review_text="great",
    )

    agg.mark_valid(is_valid=True, reason=None)
    agg.mark_stored()
    agg.update_station_average(new_average=4.5)
    agg.publish_review()

    ev_types = [type(e).__name__ for e in agg.events]
    assert "RatingValidated" in ev_types
    assert "RatingStored" in ev_types
    assert "StationsAvgRatingUpdated" in ev_types
    assert "ReviewPublished" in ev_types
    assert "RatingMadeVisibleToUsers" in ev_types
