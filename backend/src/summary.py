from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

from livekit.agents.llm import LLM, ChatContext

from . import transcript
from .config import DATA_DIR

logger = logging.getLogger("call-summary")

SUMMARY_DIR = DATA_DIR / "summaries"

_SUMMARY_PROMPT = """You are summarizing a phone call between a dental clinic's
voice agent and a caller. Write a concise summary for the staff.

Cover, in 4-6 short lines:
- Caller's intent and requested service.
- Whether an appointment was booked, and if so the day, time, and name.
- Any follow-up the caller still needs.

Keep it factual. If something was not discussed, omit it.

Transcript:
{transcript}"""


async def generate_summary(llm: LLM, history: ChatContext) -> str:
    body = transcript.render(history)
    if not body:
        return "No conversation took place."

    prompt_ctx = ChatContext.empty()
    prompt_ctx.add_message(
        role="user", content=_SUMMARY_PROMPT.format(transcript=body)
    )

    parts: list[str] = []
    try:
        stream = llm.chat(chat_ctx=prompt_ctx)
        async for chunk in stream:
            if chunk.delta and chunk.delta.content:
                parts.append(chunk.delta.content)
        await stream.aclose()
    except Exception:
        logger.exception("Failed to generate call summary")
        return "Summary unavailable (LLM error). Raw transcript was captured."

    return "".join(parts).strip() or "Summary was empty."


def persist_summary(room_name: str, text: str) -> Path:
    SUMMARY_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = SUMMARY_DIR / f"{stamp}_{room_name}.txt"
    path.write_text(text, encoding="utf-8")
    return path
