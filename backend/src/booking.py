from __future__ import annotations

import asyncio
import re
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from . import db


@dataclass(frozen=True)
class Slot:
    slot_id: int
    slot_date: str
    slot_time: str


@dataclass(frozen=True)
class BookingResult:
    ok: bool
    message: str
    appointment_id: int | None = None
    slot: Slot | None = None


class SlotUnavailableError(Exception):
    pass


_TIME_RE = re.compile(
    r"^\s*(?P<hour>\d{1,2})(?::(?P<minute>\d{2}))?\s*(?:o'clock)?\s*(?P<period>a\.?m\.?|p\.?m\.?)?\.?\s*$",
    re.IGNORECASE,
)
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SLASH_DATE_RE = re.compile(r"^(?P<month>\d{1,2})/(?P<day>\d{1,2})(?:/(?P<year>\d{2,4}))?$")
_WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}
_NUMBER_WORDS = {
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
    "nine": "9",
    "ten": "10",
    "eleven": "11",
    "twelve": "12",
}


def normalize_slot_date(value: str, today: date | None = None) -> str | None:
    today = today or date.today()
    cleaned = value.strip().lower().rstrip(".")
    cleaned = cleaned.removeprefix("on ").strip()

    if _DATE_RE.match(cleaned):
        return cleaned
    if cleaned == "today":
        return today.isoformat()
    if cleaned == "tomorrow":
        return (today + timedelta(days=1)).isoformat()

    if cleaned.startswith("next "):
        weekday_name = cleaned.removeprefix("next ").strip()
        force_next_week = True
    else:
        weekday_name = cleaned
        force_next_week = False

    if weekday_name in _WEEKDAYS:
        target = _WEEKDAYS[weekday_name]
        days_ahead = (target - today.weekday()) % 7
        if force_next_week:
            days_ahead = days_ahead or 7
        return (today + timedelta(days=days_ahead)).isoformat()

    slash = _SLASH_DATE_RE.match(cleaned)
    if slash:
        year_value = slash.group("year")
        year = today.year if year_value is None else int(year_value)
        if year < 100:
            year += 2000
        try:
            return date(
                year, int(slash.group("month")), int(slash.group("day"))
            ).isoformat()
        except ValueError:
            return None

    return None


def normalize_slot_time(value: str) -> str | None:
    cleaned = value.strip().lower()
    cleaned = cleaned.replace("-", " ")
    for word, number in _NUMBER_WORDS.items():
        cleaned = re.sub(rf"\b{word}\b", number, cleaned)
    if cleaned in {"noon", "midday"}:
        return "12:00"
    if cleaned in {"midnight"}:
        return "00:00"

    match = _TIME_RE.match(cleaned)
    if match is None:
        return None

    hour = int(match.group("hour"))
    minute = int(match.group("minute") or "0")
    period = match.group("period")

    if minute > 59:
        return None

    if period:
        if hour < 1 or hour > 12:
            return None
        if period.lower().startswith("p") and hour != 12:
            hour += 12
        elif period.lower().startswith("a") and hour == 12:
            hour = 0
    elif hour > 23:
        return None

    return f"{hour:02d}:{minute:02d}"


class BookingService:
    async def available(self, slot_date: str, limit: int = 6) -> list[Slot]:
        return await asyncio.to_thread(self._sync_list, slot_date, limit)

    async def book(
        self,
        slot_date: str,
        slot_time: str,
        customer_name: str,
        service: str,
        phone: str | None = None,
    ) -> BookingResult:
        return await asyncio.to_thread(
            self._sync_book, slot_date, slot_time, customer_name, service, phone
        )

    def _sync_list(self, slot_date: str, limit: int) -> list[Slot]:
        normalized_date = normalize_slot_date(slot_date)
        if normalized_date is None:
            return []

        conn = db.connect()
        try:
            rows = conn.execute(
                """
                SELECT id, slot_date, slot_time
                FROM slots
                WHERE slot_date = ? AND is_booked = 0
                ORDER BY slot_time
                LIMIT ?
                """,
                (normalized_date, limit),
            ).fetchall()
        finally:
            conn.close()
        return [Slot(r["id"], r["slot_date"], r["slot_time"]) for r in rows]

    def _sync_book(
        self,
        slot_date: str,
        slot_time: str,
        customer_name: str,
        service: str,
        phone: str | None,
    ) -> BookingResult:
        normalized_date = normalize_slot_date(slot_date)
        if normalized_date is None:
            return BookingResult(
                ok=False,
                message=f"Could not understand the requested date '{slot_date}'.",
            )

        normalized_time = normalize_slot_time(slot_time)
        if normalized_time is None:
            return BookingResult(
                ok=False,
                message=f"Could not understand the requested time '{slot_time}'.",
            )

        conn = db.connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            cursor = conn.execute(
                """
                UPDATE slots
                SET is_booked = 1
                WHERE slot_date = ? AND slot_time = ? AND is_booked = 0
                """,
                (normalized_date, normalized_time),
            )

            if cursor.rowcount == 0:
                row = conn.execute(
                    """
                    SELECT id, is_booked FROM slots
                    WHERE slot_date = ? AND slot_time = ?
                    """,
                    (normalized_date, normalized_time),
                ).fetchone()
                conn.rollback()

                if row is None:
                    open_rows = conn.execute(
                        """
                        SELECT slot_time FROM slots
                        WHERE slot_date = ? AND is_booked = 0
                        ORDER BY slot_time
                        """,
                        (normalized_date,),
                    ).fetchall()
                    open_times = ", ".join(r["slot_time"] for r in open_rows)
                    suffix = f" Open times are: {open_times}." if open_times else ""
                    return BookingResult(
                        ok=False,
                        message=(
                            f"No slot exists on {normalized_date} at {normalized_time}."
                            f"{suffix}"
                        ),
                    )

                return BookingResult(
                    ok=False,
                    message=f"The {normalized_time} slot on {normalized_date} is already taken.",
                )

            row = conn.execute(
                """
                SELECT id FROM slots
                WHERE slot_date = ? AND slot_time = ?
                """,
                (normalized_date, normalized_time),
            ).fetchone()

            slot_id = row["id"]
            cursor = conn.execute(
                """
                INSERT INTO appointments
                    (slot_id, customer_name, service, phone, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    slot_id,
                    customer_name,
                    service,
                    phone,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            conn.commit()
            return BookingResult(
                ok=True,
                message=f"Booked {service} for {customer_name} on {normalized_date} at {normalized_time}.",
                appointment_id=cursor.lastrowid,
                slot=Slot(slot_id, normalized_date, normalized_time),
            )
        except sqlite3.IntegrityError:
            conn.rollback()
            return BookingResult(
                ok=False,
                message=f"The {normalized_time} slot on {normalized_date} was just taken.",
            )
        finally:
            conn.close()
