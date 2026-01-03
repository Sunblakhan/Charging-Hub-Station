import sqlite3
from typing import Iterable, Optional
from uuid import UUID

from src.malfunction.domain.value_objects.Name import Name
from src.malfunction.domain.entities.Incident import Incident
from src.malfunction.domain.value_objects.Email import Email
from src.malfunction.domain.value_objects.StationLabel import StationLabel
from src.malfunction.domain.value_objects.ProblemDescription import ProblemDescription


class IncidentRepository:
    """
    SQLite repository for Incident entities.
    """

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS incidents (
                id TEXT PRIMARY KEY,
                reporter_name TEXT NOT NULL,
                reporter_email TEXT NOT NULL,
                station_label TEXT NOT NULL,
                description TEXT NOT NULL,
                is_valid INTEGER NOT NULL,
                is_solved INTEGER NOT NULL,
                points_awarded INTEGER NOT NULL,
                status TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def save(self, incident: Incident) -> None:
        self._conn.execute(
            """
            INSERT OR REPLACE INTO incidents
            (id, reporter_name, reporter_email, station_label, description,
             is_valid, is_solved, points_awarded, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(incident.id),
                incident.reporter_name.value,
                incident.reporter_email.value,
                incident.station_label.value,
                incident.description.value,
                int(incident.is_valid),
                int(incident.is_solved),
                incident.points_awarded,
                incident.status,
            ),
        )
        self._conn.commit()

    def get_by_id(self, id_: UUID) -> Optional[Incident]:
        row = self._conn.execute(
            """
            SELECT id, reporter_name, reporter_email, station_label, description,
                   is_valid, is_solved, points_awarded, status
            FROM incidents
            WHERE id = ?
            """,
            (str(id_),),
        ).fetchone()

        if row is None:
            return None

        return Incident(
            id=UUID(row[0]),
            reporter_name=Name(row[1]),
            reporter_email=Email(row[2]),
            station_label=StationLabel(row[3]),
            description=ProblemDescription(row[4]),
            is_valid=bool(row[5]),
            is_solved=bool(row[6]),
            points_awarded=row[7],
            status=row[8],
        )

    def list_pending(self) -> Iterable[Incident]:
        rows = self._conn.execute(
            """
            SELECT id, reporter_name, reporter_email, station_label, description,
                   is_valid, is_solved, points_awarded, status
            FROM incidents
            WHERE status = 'PENDING'
            """
        ).fetchall()

        for row in rows:
            yield Incident(
                id=UUID(row[0]),
                reporter_name=Name(row[1]),
                reporter_email=Email(row[2]),
                station_label=StationLabel(row[3]),
                description=ProblemDescription(row[4]),
                is_valid=bool(row[5]),
                is_solved=bool(row[6]),
                points_awarded=row[7],
                status=row[8],
            )
            
    # --- ADD THESE METHODS TO IncidentRepository ---

    # In IncidentRepository.py

    def get_by_station(self, station_label: str):
        rows = self._conn.execute(
            """
            SELECT id, reporter_name, reporter_email, station_label, description,
                   is_valid, is_solved, points_awarded, status
            FROM incidents
            WHERE station_label = ?
            ORDER BY rowid DESC
            """,
            (station_label,)
        ).fetchall()

        # Convert DB rows back to Incident Objects
        results = []
        for row in rows:
            results.append(Incident(
                id=UUID(row[0]),
                reporter_name=Name(row[1]),
                reporter_email=Email(row[2]),
                station_label=StationLabel(row[3]),
                description=ProblemDescription(row[4]),
                is_valid=bool(row[5]),
                is_solved=bool(row[6]),
                points_awarded=row[7],
                status=row[8],
            ))
        return results

    def update_status(self, incident_id: str, is_valid: bool, is_solved: bool) -> None:
        status_text = "PENDING"
        if is_solved:
            status_text = "SOLVED"
        elif is_valid:
            status_text = "IN_PROGRESS"
            
        self._conn.execute(
            """
            UPDATE incidents
            SET is_valid = ?, is_solved = ?, status = ?
            WHERE id = ?
            """,
            (int(is_valid), int(is_solved), status_text, incident_id)
        )
        self._conn.commit()
        
    # --- ADD TO IncidentRepository.py ---

    def get_all(self) -> Iterable[Incident]:
        """Fetches ALL incidents for the Admin view."""
        rows = self._conn.execute(
            """
            SELECT id, reporter_name, reporter_email, station_label, description,
                   is_valid, is_solved, points_awarded, status
            FROM incidents
            ORDER BY rowid DESC
            """
        ).fetchall()

        for row in rows:
            yield Incident(
                id=UUID(row[0]),
                reporter_name=Name(row[1]),
                reporter_email=Email(row[2]),
                station_label=StationLabel(row[3]),
                description=ProblemDescription(row[4]),
                is_valid=bool(row[5]),
                is_solved=bool(row[6]),
                points_awarded=row[7],
                status=row[8],
            )
