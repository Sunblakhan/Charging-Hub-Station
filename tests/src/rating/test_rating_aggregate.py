import pytest

from src.rating.domain.aggregates.RatingAggregate import RatingAggregate


# ===================== HAPPY PATH: EVENT EMISSION =====================

def test_create_new_emits_basic_events():
    """AGGREGATE: Factory method should emit creation events."""
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


# ===================== WORKFLOW: EVENT ORDERING =====================

def test_validation_and_publish_events():
    """AGGREGATE: Complete workflow should emit events in correct order."""
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
    
    # Verify event order in workflow
    selection_idx = ev_types.index("SelectChargingStation")
    creation_idx = ev_types.index("NewRatingCreated")
    submission_idx = ev_types.index("RatingSubmitted")
    validation_idx = ev_types.index("RatingValidated")
    stored_idx = ev_types.index("RatingStored")
    avg_idx = ev_types.index("StationsAvgRatingUpdated")
    published_idx = ev_types.index("ReviewPublished")
    visible_idx = ev_types.index("RatingMadeVisibleToUsers")

    # Assertions follow workflow order
    assert selection_idx < creation_idx < submission_idx, "Creation events out of order"
    assert submission_idx < validation_idx < stored_idx, "Validation/storage out of order"
    assert stored_idx < avg_idx < published_idx, "Publishing/average out of order"
    assert published_idx < visible_idx, "Final visibility event out of order"


# ===================== VALIDATION: INVALID BRANCH =====================

def test_mark_valid_false_with_reason():
    """AGGREGATE: Should emit RatingValidated with is_valid=False."""
    agg = RatingAggregate.create_new(
        rating_id="r3",
        user_id="u3",
        user_name="Charlie",
        user_email="charlie@example.com",
        station_label="Berliner Stadtwerke KommunalPartner GmbH - Leipziger Platz 19, 1011 Berlin",
        stars=3,
        review_text="ok",
    )

    agg.mark_valid(is_valid=False, reason="Email already submitted a rating today")

    # Find the RatingValidated event
    validation_event = next(
        e for e in agg.events if type(e).__name__ == "RatingValidated"
    )

    assert validation_event.is_valid == False
    assert validation_event.reason == "Email already submitted a rating today"


# ===================== ENTITY STATE: VALUE OBJECTS =====================

def test_aggregate_preserves_all_user_inputs():
    """ENTITY: Aggregate should preserve all user-provided data."""
    agg = RatingAggregate.create_new(
        rating_id="r4",
        user_id="u4",
        user_name="Diana",
        user_email="diana@example.com",
        station_label="TotalEnergies Charging Solutions - Storkower Str. 175, 1036 Berlin",
        stars=1,  # minimum rating
        review_text="terrible service",
    )

    rating = agg.rating
    assert rating.rating_id == "r4"
    assert rating.user_id.value == "u4"
    assert rating.name.value == "Diana"
    assert rating.email.value == "diana@example.com"
    assert rating.station_label.value == "TotalEnergies Charging Solutions - Storkower Str. 175, 1036 Berlin"
    assert rating.stars.value == 1
    assert rating.review.value == "terrible service"


def test_aggregate_with_optional_review_none():
    """ENTITY: Aggregate should handle None review gracefully."""
    agg = RatingAggregate.create_new(
        rating_id="r5",
        user_id="u5",
        user_name="Eve",
        user_email="eve@example.com",
        station_label="Berliner Stadtwerke KommunalPartner GmbH - Leipziger Platz 19, 1011 Berlin",
        stars=4,
        review_text=None,
    )

    assert agg.rating.review.value is None

    # Verify event shows empty string (as per current implementation)
    new_rating_event = next(
        e for e in agg.events if type(e).__name__ == "NewRatingCreated"
    )
    assert new_rating_event.review_text == "" or new_rating_event.review_text is None


# ===================== IMMUTABILITY: FROZEN VALUE OBJECTS =====================

def test_rating_entity_created_at_immutable():
    """VALUE OBJECT: created_at should be set and not change."""
    from datetime import datetime, UTC
    
    now = datetime.now(UTC)
    agg = RatingAggregate.create_new(
        rating_id="r6",
        user_id="u6",
        user_name="Frank",
        user_email="frank@example.com",
        station_label="Design Offices GmbH (Köln) - Gartenstraße 87, 10115 Berlin",
        stars=5,
        review_text="excellent",
        created_at=now,
    )

    assert agg.rating.created_at == now


# ===================== VALUE OBJECT CONSTRAINTS =====================

def test_aggregate_rejects_invalid_email_on_create():
    """AGGREGATE INVARIANT: Should reject invalid email at creation."""
    import pytest
    
    with pytest.raises(ValueError):
        RatingAggregate.create_new(
            rating_id="r7",
            user_id="u7",
            user_name="Grace",
            user_email="invalid-email",  # Missing @ and domain
            station_label="Berliner Stadtwerke KommunalPartner GmbH - Leipziger Platz 19, 1011 Berlin",
            stars=3,
            review_text="test",
        )


def test_aggregate_rejects_invalid_stars_on_create():
    """AGGREGATE INVARIANT: Should reject invalid star rating at creation."""
    
    with pytest.raises(ValueError):
        RatingAggregate.create_new(
            rating_id="r8",
            user_id="u8",
            user_name="Henry",
            user_email="henry@example.com",
            station_label="Berliner Stadtwerke KommunalPartner GmbH - Leipziger Platz 19, 1011 Berlin",
            stars=10,  # Invalid: must be 1-5
            review_text="test",
        )


def test_aggregate_rejects_empty_name_on_create():
    """AGGREGATE INVARIANT: Should reject empty name at creation."""
    
    with pytest.raises(ValueError):
        RatingAggregate.create_new(
            rating_id="r9",
            user_id="u9",
            user_name="",  # Empty
            user_email="iris@example.com",
            station_label="Berliner Stadtwerke KommunalPartner GmbH - Leipziger Platz 19, 1011 Berlin",
            stars=4,
            review_text="test",
        )


# ===================== EVENTS IMMUTABILITY =====================

def test_events_list_is_copy():
    """AGGREGATE: events property should return a copy, not reference."""
    agg = RatingAggregate.create_new(
        rating_id="r10",
        user_id="u10",
        user_name="Jack",
        user_email="jack@example.com",
        station_label="Design Offices GmbH (Köln) - Gartenstraße 87, 10115 Berlin",
        stars=5,
        review_text="great",
    )

    events1 = agg.events
    events2 = agg.events

    # Should be equal but different objects
    assert events1 == events2
    assert events1 is not events2  # Different list instances
