"use client";

import { useEffect, useRef } from "react";
import { TranscriptMessage } from "@/lib/types";

const SPEAKER = { caller: "Caller", agent: "Assistant" } as const;

export function TranscriptFeed({
  messages,
  interimCaller,
}: {
  messages: TranscriptMessage[];
  interimCaller: string | null;
}) {
  const endRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, interimCaller]);

  const empty = messages.length === 0 && !interimCaller;

  return (
    <div className="feed card">
      <p className="panel-title">Live transcript</p>
      <div className="feed-scroll">
        {empty && (
          <div className="empty">
            Waiting for the conversation to begin. Start a call in another tab.
          </div>
        )}

        {messages.map((m) => (
          <div key={m.id} className={`bubble ${m.role}`}>
            <div className="speaker">{SPEAKER[m.role]}</div>
            {m.text}
          </div>
        ))}

        {interimCaller && (
          <div className="bubble interim">
            <div className="speaker">Caller</div>
            {interimCaller}
            <span className="typing" style={{ marginLeft: 6 }}>
              <span />
              <span />
              <span />
            </span>
          </div>
        )}

        <div ref={endRef} />
      </div>
    </div>
  );
}
