from __future__ import annotations

import asyncio
import json
import logging

from livekit import agents
from livekit.agents import AgentServer, AgentSession, JobContext, JobProcess
from livekit.plugins import deepgram, groq

from .booking_agent import BookingAgent
from .config import get_settings
from .db import init_db
from .lifecycle import CallLifecycle
from .monitor import MonitorPublisher
from .transfer import WarmTransfer

logger = logging.getLogger("agent")

CALLER_PREFIX = "caller"
CONTROL_TOPIC = "call-control"


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
            temperature=0.4,
            max_completion_tokens=350,
            max_retries=3,
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
        model=settings.llm_model,
        api_key=settings.groq_api_key,
        temperature=0.3,
        max_completion_tokens=300,
        max_retries=3,
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
        if getattr(item, "type", None) != "message":
            return
        if item.role == "assistant" and item.text_content:
            monitor.agent_transcript(item.text_content)

    @session.on("metrics_collected")
    def _on_metrics(ev) -> None:
        m = ev.metrics
        kind = type(m).__name__
        try:
            if kind == "LLMMetrics":
                tps = getattr(m, "tokens_per_second", 0) or 0
                monitor.metric(
                    "LLM", m.label, (m.ttft or 0) * 1000,
                    f"{m.total_tokens} tok · {tps:.0f} tok/s",
                )
            elif kind == "TTSMetrics":
                monitor.metric(
                    "TTS", m.label, (m.ttfb or 0) * 1000,
                    f"{m.audio_duration:.1f}s audio",
                )
            elif kind == "STTMetrics":
                monitor.metric("STT", m.label, (m.duration or 0) * 1000, None)
            elif kind == "EOUMetrics":
                monitor.metric(
                    "Turn", "endpointing",
                    (m.end_of_utterance_delay or 0) * 1000, "end of turn",
                )
        except Exception:
            logger.debug("metric publish failed", exc_info=True)

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

    async def end_everything() -> None:
        try:
            await ctx.delete_room()
        except Exception:
            logger.warning("failed to delete room", exc_info=True)

    @ctx.room.on("participant_disconnected")
    def _on_leave(participant) -> None:
        identity = participant.identity
        if lifecycle.transferred:
            logger.info("%s left after transfer; ending call", identity)
            asyncio.create_task(end_everything())
        elif identity.startswith(CALLER_PREFIX):
            logger.info("caller %s left; ending call", identity)
            asyncio.create_task(lifecycle.end())

    @ctx.room.on("data_received")
    def _on_data(packet) -> None:
        if packet.topic != CONTROL_TOPIC:
            return
        try:
            action = json.loads(packet.data.decode("utf-8")).get("action")
        except Exception:
            return
        if action == "end":
            logger.info("caller requested end via control channel")
            if lifecycle.transferred:
                asyncio.create_task(end_everything())
            else:
                asyncio.create_task(lifecycle.end())

    ctx.add_shutdown_callback(lifecycle.finalize)

    transfer = WarmTransfer(ctx, session, monitor, summary_llm, settings)

    async def hangup() -> None:
        await lifecycle.end()

    async def do_transfer(reason: str) -> bool:
        ok = await transfer.start(reason)
        if ok:
            lifecycle.mark_transferred()
        return ok

    agent = BookingAgent(
        monitor=monitor, on_hangup=hangup, on_transfer=do_transfer
    )
    await session.start(agent=agent, room=ctx.room)
    for participant in ctx.room.remote_participants.values():
        _remember_caller(participant.identity)
    monitor.call_status("connected")

    await session.say(
        f"Hi, thanks for calling {settings.business_name}. "
        "I can help you book an appointment. How can I help today?"
    )


if __name__ == "__main__":
    agents.cli.run_app(server)
