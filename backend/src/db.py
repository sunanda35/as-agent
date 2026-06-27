from __future__ import annotations

import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

from .config import DATA_DIR, DB_PATH

DEFAULT_SLOT_TIMES = ("09:00", "10:00", "11:00", "14:00", "15:00", "16:00")
SEED_BUSINESS_DAYS = 14


def connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS slots (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            slot_date TEXT NOT NULL,
            slot_time TEXT NOT NULL,
            is_booked INTEGER NOT NULL DEFAULT 0,
            UNIQUE (slot_date, slot_time)
        );

        CREATE TABLE IF NOT EXISTS appointments (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            slot_id       INTEGER NOT NULL UNIQUE REFERENCES slots(id),
            customer_name TEXT NOT NULL,
            service       TEXT NOT NULL,
            phone         TEXT,
            created_at    TEXT NOT NULL,
            FOREIGN KEY (slot_id) REFERENCES slots(id)
        );
        """
    )


def _next_business_days(count: int, start: date) -> list[date]:
    days: list[date] = []
    cursor = start
    while len(days) < count:
        if cursor.weekday() < 5:
            days.append(cursor)
        cursor += timedelta(days=1)
    return days


def _seed_slots(conn: sqlite3.Connection) -> None:
    already_seeded = conn.execute("SELECT COUNT(*) FROM slots").fetchone()[0]
    if already_seeded:
        return
    rows = [
        (day.isoformat(), slot_time)
        for day in _next_business_days(SEED_BUSINESS_DAYS, date.today())
        for slot_time in DEFAULT_SLOT_TIMES
    ]
    conn.executemany(
        "INSERT INTO slots (slot_date, slot_time) VALUES (?, ?)", rows
    )


def init_db() -> Path:
    conn = connect()
    try:
        _create_schema(conn)
        _seed_slots(conn)
        conn.commit()
    finally:
        conn.close()
    return DB_PATH


if __name__ == "__main__":
    path = init_db()
    print(f"Initialized database at {path}")
