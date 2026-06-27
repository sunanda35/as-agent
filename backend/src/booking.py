from __future__ import annotations

import asyncio
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone

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
                (slot_date, limit),
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
        conn = db.connect()
        try:
            row = conn.execute(
                """
                SELECT id, is_booked FROM slots
                WHERE slot_date = ? AND slot_time = ?
                """,
                (slot_date, slot_time),
            ).fetchone()

            if row is None:
                return BookingResult(
                    ok=False,
                    message=f"No slot exists on {slot_date} at {slot_time}.",
                )
            if row["is_booked"]:
                return BookingResult(
                    ok=False,
                    message=f"The {slot_time} slot on {slot_date} is already taken.",
                )

            slot_id = row["id"]
            conn.execute(
                "UPDATE slots SET is_booked = 1 WHERE id = ? AND is_booked = 0",
                (slot_id,),
            )
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
                message=f"Booked {service} for {customer_name} on {slot_date} at {slot_time}.",
                appointment_id=cursor.lastrowid,
                slot=Slot(slot_id, slot_date, slot_time),
            )
        except sqlite3.IntegrityError:
            conn.rollback()
            return BookingResult(
                ok=False,
                message=f"The {slot_time} slot on {slot_date} was just taken.",
            )
        finally:
            conn.close()
