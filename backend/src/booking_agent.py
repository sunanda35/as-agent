from __future__ import annotations

import logging
from typing import Awaitable, Callable

from livekit.agents import Agent, RunContext, function_tool

from .booking import BookingService
from .monitor import MonitorPublisher
from .prompts import system_instructions

logger = logging.getLogger("booking-agent")


def _speakable_time(slot_time: str) -> str:
    hour, minute = (int(part) for part in slot_time.split(":"))
    suffix = "AM" if hour < 12 else "PM"
    hour_12 = hour % 12 or 12
    if minute:
        return f"{hour_12}:{minute:02d} {suffix}"
    return f"{hour_12} {suffix}"


class BookingAgent(Agent):
    def __init__(
        self,
        booking: BookingService | None = None,
        monitor: MonitorPublisher | None = None,
        on_hangup: Callable[[], Awaitable[None]] | None = None,
    ) -> None:
        super().__init__(instructions=system_instructions())
        self._booking = booking or BookingService()
        self._monitor = monitor
        self._on_hangup = on_hangup

    def _notify(self, label: str, status: str, detail: str | None = None) -> None:
        if self._monitor is not None:
            self._monitor.action(label, status, detail)

    @function_tool
    async def check_availability(
        self, context: RunContext, day: str
    ) -> dict:
        """Look up open appointment times for a given day.

        Args:
            day: The date to check, as an ISO string in YYYY-MM-DD format.
        """
        self._notify("Checking availability", "running", day)
        slots = await self._booking.available(day)
        logger.info("check_availability day=%s found=%d", day, len(slots))
        self._notify(
            "Checking availability", "done", f"{len(slots)} open on {day}"
        )
        if not slots:
            return {
                "day": day,
                "available": False,
                "times": [],
                "note": "No open times on that day. Suggest another weekday.",
            }
        return {
            "day": day,
            "available": True,
            "times": [_speakable_time(s.slot_time) for s in slots],
            "raw_times": [s.slot_time for s in slots],
        }

    @function_tool
    async def book_appointment(
        self,
        context: RunContext,
        day: str,
        time: str,
        customer_name: str,
        service: str,
    ) -> dict:
        """Book an appointment in an open slot.

        Args:
            day: The appointment date as an ISO string in YYYY-MM-DD format.
            time: The 24-hour slot time as HH:MM, taken from check_availability.
            customer_name: The caller's full name.
            service: The requested service, e.g. checkup or cleaning.
        """
        self._notify("Booking appointment", "running", f"{customer_name} · {day} {time}")
        result = await self._booking.book(day, time, customer_name, service)
        self._notify(
            "Booking appointment",
            "done" if result.ok else "failed",
            result.message,
        )
        logger.info(
            "book_appointment day=%s time=%s name=%s ok=%s",
            day,
            time,
            customer_name,
            result.ok,
        )
        return {
            "booked": result.ok,
            "message": result.message,
            "appointment_id": result.appointment_id,
            "spoken_time": _speakable_time(time) if result.ok else None,
        }

    @function_tool
    async def end_call(self, context: RunContext, farewell: str) -> dict:
        """End the phone call when the caller says goodbye or confirms they need
        nothing else. Always speak a short, warm closing line.

        Args:
            farewell: A brief friendly sign-off to say before hanging up.
        """
        logger.info("end_call requested")
        handle = context.session.say(farewell, allow_interruptions=False)
        await handle.wait_for_playout()
        if self._on_hangup is not None:
            await self._on_hangup()
        return {"ended": True}
