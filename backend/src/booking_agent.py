from __future__ import annotations

import logging
from typing import Awaitable, Callable

from livekit.agents import Agent, RunContext, function_tool

from .booking import BookingService, normalize_slot_date
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
        on_transfer: Callable[[str], Awaitable[bool]] | None = None,
    ) -> None:
        super().__init__(instructions=system_instructions())
        self._booking = booking or BookingService()
        self._monitor = monitor
        self._on_hangup = on_hangup
        self._on_transfer = on_transfer

    def _notify(self, label: str, status: str, detail: str | None = None) -> None:
        if self._monitor is not None:
            self._monitor.action(label, status, detail)

    @function_tool
    async def note_intent(self, context: RunContext, intent: str) -> dict:
        """Record what the caller wants, as soon as you understand it. Call this
        once, early in the call, before checking availability.

        Args:
            intent: A short phrase describing the caller's goal, e.g.
                "Book a dental cleaning" or "Reschedule an appointment".
        """
        logger.info("intent detected: %s", intent)
        if self._monitor is not None:
            self._monitor.intent(intent)
        return {"noted": True}

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
        normalized_day = slots[0].slot_date if slots else normalize_slot_date(day) or day
        logger.info("check_availability day=%s found=%d", day, len(slots))
        self._notify(
            "Checking availability", "done", f"{len(slots)} open on {normalized_day}"
        )
        if not slots:
            return {
                "day": normalized_day,
                "available": False,
                "times": [],
                "note": "No open times on that day. Suggest another weekday.",
            }
        return {
            "day": normalized_day,
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
        contact_number: str,
    ) -> dict:
        """Book an appointment in an open slot. Only call this after you have
        collected the caller's name, reason for visit, preferred time, and a
        contact phone number, and confirmed the slot is available.

        Args:
            day: The appointment date as an ISO string in YYYY-MM-DD format.
            time: The 24-hour slot time as HH:MM, taken from check_availability.
            customer_name: The caller's full name.
            service: The reason for the visit, e.g. checkup or cleaning.
            contact_number: The caller's contact phone number.
        """
        self._notify("Booking appointment", "running", f"{customer_name} · {day} {time}")
        result = await self._booking.book(
            day, time, customer_name, service, phone=contact_number
        )
        self._notify(
            "Booking appointment",
            "done" if result.ok else "failed",
            result.message,
        )
        logger.info(
            "book_appointment day=%s time=%s name=%s phone=%s ok=%s",
            day,
            time,
            customer_name,
            contact_number,
            result.ok,
        )
        return {
            "booked": result.ok,
            "message": result.message,
            "appointment_id": result.appointment_id,
            "spoken_time": _speakable_time(result.slot.slot_time)
            if result.ok and result.slot is not None
            else None,
        }

    @function_tool
    async def transfer_to_human(self, context: RunContext, reason: str) -> dict:
        """Warm-transfer the caller to a human teammate. Use this when the caller
        asks to speak to a person, or for billing questions or complaints that you
        cannot resolve. Do not promise a transfer you have not started.

        Args:
            reason: A short reason for the transfer, e.g. "a billing question"
                or "a complaint about a recent visit".
        """
        logger.info("transfer_to_human requested: %s", reason)
        if self._on_transfer is None:
            return {"transferred": False, "message": "Transfer is not available."}
        transferred = await self._on_transfer(reason)
        return {"transferred": transferred}

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
