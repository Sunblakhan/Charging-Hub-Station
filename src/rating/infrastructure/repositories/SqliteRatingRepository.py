import sqlite3
from typing import List
from uuid import uuid4
from datetime import datetime

from src.rating.domain.entities.Rating import Rating
from src.rating.infrastructure.repositories.RatingRepositoryInterface import (
    RatingRepositoryInterface,
)


class SqliteRatingRepository(RatingRepositoryInterface):
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self._init_schema()

    def _init_schema(self) -> None:
        cur = self._conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS ratings (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                station_label TEXT NOT NULL,
                stars INTEGER NOT NULL,
                review_text TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    # -------- interface methods --------

    def next_id(self) -> str:
        return str(uuid4())

    def save(self, rating: Rating) -> None:
        cur = self._conn.cursor()
        cur.execute(
            """
            INSERT INTO ratings
                (id, user_id, name, email, station_label, stars, review_text, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                rating.rating_id,
                rating.user_id.value,
                rating.name.value,
                rating.email.value,
                rating.station_label.value,
                rating.stars.value,
                rating.review.value,
                rating.created_at.isoformat(),
            ),
        )
        self._conn.commit()

    def all_for_station(self, station_label: str) -> List[Rating]:
        cur = self._conn.cursor()
        cur.execute(
            """
            SELECT id, user_id, name, email, station_label, stars, review_text, created_at
            FROM ratings
            WHERE station_label = ?
            """,
            (station_label,),
        )
        rows = cur.fetchall()

        ratings: List[Rating] = []
        for row in rows:
            (
                rating_id,
                user_id,
                name,
                email,
                station_label,
                stars,
                review_text,
                created_at,
            ) = row
            ratings.append(
                Rating.from_primitives(
                    rating_id=rating_id,
                    user_id=user_id,
                    name=name,
                    email=email,
                    station_label=station_label,
                    stars=stars,
                    review_text=review_text,
                    created_at=datetime.fromisoformat(created_at),
                )
            )
        return ratings

    def all(self) -> list[Rating]:
        cur = self._conn.cursor()
        cur.execute(
            """
            SELECT id, user_id, name, email, station_label, stars, review_text, created_at
            FROM ratings
            """
        )
        rows = cur.fetchall()
        ratings: list[Rating] = []
        for (
            rating_id,
            user_id,
            name,
            email,
            station_label,
            stars,
            review_text,
            created_at,
        ) in rows:
            ratings.append(
                Rating.from_primitives(
                    rating_id=rating_id,
                    user_id=user_id,
                    name=name,
                    email=email,
                    station_label=station_label,
                    stars=stars,
                    review_text=review_text,
                    created_at=datetime.fromisoformat(created_at),
                )
            )
        return ratings