from __future__ import annotations

import logging
from datetime import timedelta

from livekit import api
from livekit.agents import AgentSession, JobContext
from livekit.agents.llm import LLM

from .config import Settings
from .monitor import MonitorPublisher

logger = logging.getLogger("transfer")

HUMAN_IDENTITY = "human-agent"
RING_SECONDS = 25


class WarmTransfer:
    def __init__(
        self,
        ctx: JobContext,
        session: AgentSession,
        monitor: MonitorPublisher,
        summary_llm: LLM,
        settings: Settings,
    ) -> None:
        self._ctx = ctx
        self._session = session
        self._monitor = monitor
        self._summary_llm = summary_llm
        self._settings = settings

    async def _say(self, text: str, interruptible: bool = False) -> None:
        handle = self._session.say(text, allow_interruptions=interruptible)
        await handle.wait_for_playout()

    async def _unavailable(self) -> None:
        self._monitor.action("Transfer", "failed", "Teammate unavailable")
        self._monitor.call_status("connected")
        await self._say(
            "I'm sorry, our team isn't available right now. "
            "Is there anything else I can help you with?",
            interruptible=True,
        )

    def _step_aside(self) -> None:
        self._session.input.set_audio_enabled(False)
        self._session.output.set_audio_enabled(False)

    async def start(self, reason: str) -> bool:
        if not self._settings.transfer_enabled:
            logger.info("transfer requested but not configured")
            await self._unavailable()
            return False

        self._monitor.call_status("transferring")
        self._monitor.action("Transferring to a teammate", "running", reason)
        await self._say(
            f"Sure, let me connect you with a team member about {reason}. "
            "Please stay on the line."
        )

        try:
            await self._ctx.api.sip.create_sip_participant(
                api.CreateSIPParticipantRequest(
                    sip_trunk_id=self._settings.sip_trunk_id,
                    sip_call_to=self._settings.transfer_phone_number,
                    room_name=self._ctx.room.name,
                    participant_identity=HUMAN_IDENTITY,
                    participant_name="Human Agent",
                    wait_until_answered=True,
                    ringing_timeout=timedelta(seconds=RING_SECONDS),
                )
            )
        except Exception:
            logger.warning("warm transfer dial failed", exc_info=True)
            await self._unavailable()
            return False

        self._monitor.action("Transferring to a teammate", "done", "Teammate connected")
        await self._say(
            f"Hi, I'm connecting a caller who needs help with {reason}. "
            "They're on the line now — go ahead."
        )
        self._step_aside()
        logger.info("warm transfer completed for reason=%s", reason)
        return True
