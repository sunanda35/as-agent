from __future__ import annotations

import asyncio
import logging

from livekit import agents
from livekit.agents import AgentServer, AgentSession, JobContext, JobProcess
from livekit.plugins import deepgram, groq

from .booking_agent import BookingAgent
from .config import get_settings
from .db import init_db
from .lifecycle import CallLifecycle
from .monitor import MonitorPublisher

logger = logging.getLogger("agent")

CALLER_PREFIX = "caller"


def _build_session() -> AgentSession:
    settings = get_settings()
    return AgentSession(
        stt=deepgram.STT(
            model=settings.stt_model,
            language="en-US",
            api_key=settings.deepgram_api_key,
        ),
        llm=groq.LLM(
            model=settings.llm_model,
            api_key=settings.groq_api_key,
        ),
        tts=deepgram.TTS(
            model=settings.tts_model,
            api_key=settings.deepgram_api_key,
        ),
    )


def on_setup(_: JobProcess) -> None:
    init_db()


server = AgentServer(setup_fnc=on_setup)


@server.rtc_session(agent_name="booking-agent")
async def booking_session(ctx: JobContext) -> None:
    settings = get_settings()
    await ctx.connect()

    session = _build_session()
    monitor = MonitorPublisher(ctx.room)
    summary_llm = groq.LLM(
        model=settings.llm_model, api_key=settings.groq_api_key
    )
    lifecycle = CallLifecycle(ctx, session, monitor, summary_llm)

    @session.on("agent_state_changed")
    def _on_state(ev) -> None:
        monitor.state(ev.new_state)

    @session.on("user_input_transcribed")
    def _on_user_transcript(ev) -> None:
        monitor.user_transcript(ev.transcript, ev.is_final)

    @session.on("conversation_item_added")
    def _on_item(ev) -> None:
        item = ev.item
        if item.role == "assistant" and item.text_content:
            monitor.agent_transcript(item.text_content)

    @session.on("error")
    def _on_error(ev) -> None:
        logger.error("session error: %s", ev)

    @session.on("close")
    def _on_close(ev) -> None:
        logger.info("session closed: %s", getattr(ev, "reason", ev))

    caller = {"identity": None}

    def _remember_caller(identity: str) -> None:
        if identity.startswith(CALLER_PREFIX):
            caller["identity"] = identity

    @ctx.room.on("participant_connected")
    def _on_join(participant) -> None:
        _remember_caller(participant.identity)

    @ctx.room.on("participant_disconnected")
    def _on_leave(participant) -> None:
        if participant.identity.startswith(CALLER_PREFIX):
            logger.info("caller %s left; ending call", participant.identity)
            asyncio.create_task(lifecycle.end())

    ctx.add_shutdown_callback(lifecycle.finalize)

    async def hangup() -> None:
        await lifecycle.hangup(caller["identity"])

    agent = BookingAgent(monitor=monitor, on_hangup=hangup)
    await session.start(agent=agent, room=ctx.room)
    for participant in ctx.room.remote_participants.values():
        _remember_caller(participant.identity)
    monitor.call_status("live")

    await session.generate_reply(
        instructions=(
            f"Greet the caller, say you are the booking assistant for "
            f"{settings.business_name}, and ask how you can help."
        )
    )


if __name__ == "__main__":
    agents.cli.run_app(server)
