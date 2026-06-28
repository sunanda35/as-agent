from __future__ import annotations

import asyncio
import logging

from livekit.agents import AgentSession, JobContext
from livekit.agents.llm import LLM

from .monitor import MonitorPublisher
from .summary import generate_summary, persist_summary

logger = logging.getLogger("lifecycle")


class CallLifecycle:
    def __init__(
        self,
        ctx: JobContext,
        session: AgentSession,
        monitor: MonitorPublisher,
        summary_llm: LLM,
    ) -> None:
        self._ctx = ctx
        self._session = session
        self._monitor = monitor
        self._summary_llm = summary_llm
        self._finalized = False
        self._ended = False
        self._transferred = False

    def mark_transferred(self) -> None:
        self._transferred = True

    @property
    def transferred(self) -> bool:
        return self._transferred

    async def finalize(self) -> None:
        if self._finalized or self._transferred:
            return
        self._finalized = True

        text = await generate_summary(self._summary_llm, self._session.history)
        path = persist_summary(self._ctx.room.name, text)

        self._monitor.summary(text)
        self._monitor.call_status("ended")
        await asyncio.sleep(0.5)

        logger.info("Call summary saved to %s", path)
        print("\n===== POST-CALL SUMMARY =====")
        print(text)
        print(f"(saved to {path})")
        print("=============================\n")

    async def end(self) -> None:
        if self._ended:
            return
        self._ended = True
        await self.finalize()
        self._ctx.shutdown(reason="call ended")
