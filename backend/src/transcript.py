from __future__ import annotations

from dataclasses import dataclass

from livekit.agents.llm import ChatContext

_SPEAKER_LABELS = {"user": "Caller", "assistant": "Agent"}


@dataclass(frozen=True)
class Turn:
    speaker: str
    text: str


def extract_turns(history: ChatContext) -> list[Turn]:
    turns: list[Turn] = []
    for item in history.items:
        if getattr(item, "type", None) != "message":
            continue
        if item.role not in _SPEAKER_LABELS:
            continue
        text = item.text_content
        if not text:
            continue
        turns.append(Turn(speaker=_SPEAKER_LABELS[item.role], text=text.strip()))
    return turns


def render(history: ChatContext) -> str:
    return "\n".join(f"{turn.speaker}: {turn.text}" for turn in extract_turns(history))
