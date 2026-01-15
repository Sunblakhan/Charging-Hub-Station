from abc import ABC, abstractmethod
from typing import List

from src.rating.domain.entities.Rating import Rating


class RatingRepositoryInterface(ABC):
    @abstractmethod
    def next_id(self) -> str:
        """Return a new unique rating ID (e.g. UUID as string)."""
        ...

    @abstractmethod
    def all(self) -> List[Rating]:
        ...

    @abstractmethod
    def save(self, rating: Rating) -> None:
        """Insert a new rating into the database."""
        ...

    @abstractmethod
    def all_for_station(self, station_label: str) -> List[Rating]:
        """Return all ratings stored for the given station."""
        ...

    @abstractmethod
    def exists_for_user_and_station(self, user_email: str, station_label: str) -> bool:
        """Return True if the user already rated the station (prevents duplicates)."""
        ...
