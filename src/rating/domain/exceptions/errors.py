"""Domain-specific business rule exceptions."""


class StationNotInBerlinError(Exception):
    """
    Raised when attempting to rate a charging station that is not located in Berlin.

    This is a core business rule: ChargeHub Berlin only accepts ratings for
    Berlin-based charging stations, regardless of UI filtering.
    """

    def __init__(self, station_label: str):
        self.station_label = station_label
        super().__init__(f"Station must be in Berlin. Got: {station_label}")


class DuplicateRatingError(Exception):
    """Raised when the same user tries to rate the same station more than once."""

    def __init__(self, user_email: str, station_label: str):
        self.user_email = user_email
        self.station_label = station_label
        super().__init__(
            f"User {user_email} has already rated station '{station_label}'"
        )
