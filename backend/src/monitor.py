from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone

from livekit import rtc

logger = logging.getLogger("monitor")

MONITOR_TOPIC = "agent-monitor"


class MonitorPublisher:
    def __init__(self, room: rtc.Room) -> None:
        self._room = room

    def state(self, value: str) -> None:
        self._emit({"kind": "state", "state": value})

    def user_transcript(self, text: str, final: bool) -> None:
        self._emit(
            {"kind": "transcript", "role": "caller", "text": text, "final": final}
        )

    def agent_transcript(self, text: str) -> None:
        self._emit(
            {"kind": "transcript", "role": "agent", "text": text, "final": True}
        )

    def intent(self, text: str) -> None:
        self._emit({"kind": "intent", "text": text})

    def metric(
        self, metric: str, label: str, ms: float | None, detail: str | None = None
    ) -> None:
        self._emit(
            {
                "kind": "metric",
                "metric": metric,
                "label": label,
                "ms": round(ms) if ms is not None else None,
                "detail": detail,
            }
        )

    def action(self, label: str, status: str, detail: str | None = None) -> None:
        self._emit(
            {"kind": "action", "label": label, "status": status, "detail": detail}
        )

    def call_status(self, status: str) -> None:
        self._emit({"kind": "call", "status": status})

    def summary(self, text: str) -> None:
        self._emit({"kind": "summary", "text": text})

    def _emit(self, payload: dict) -> None:
        payload["ts"] = datetime.now(timezone.utc).isoformat()
        try:
            asyncio.get_running_loop().create_task(self._send(payload))
        except RuntimeError:
            logger.debug("No running loop; dropping monitor event %s", payload.get("kind"))

    async def _send(self, payload: dict) -> None:
        if not self._room.isconnected():
            logger.debug("Room not connected; skipping %s", payload.get("kind"))
            return
        try:
            await self._room.local_participant.publish_data(
                json.dumps(payload).encode("utf-8"),
                reliable=True,
                topic=MONITOR_TOPIC,
            )
            logger.info("monitor -> %s", payload.get("kind"))
        except Exception:
            logger.warning("Failed to publish monitor event", exc_info=True)
