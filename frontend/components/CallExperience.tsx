"use client";

import {
  RoomAudioRenderer,
  useConnectionState,
  useRoomContext,
  useVoiceAssistant,
} from "@livekit/components-react";
import { ConnectionState } from "livekit-client";
import { useMonitorEvents } from "@/lib/useMonitorEvents";
import { TranscriptFeed } from "./TranscriptFeed";

const STATUS: Record<string, string> = {
  initializing: "Connecting you to the assistant…",
  listening: "Listening — go ahead and speak",
  thinking: "One moment, working that out…",
  speaking: "The assistant is replying",
  idle: "Ready when you are",
  away: "Still there? Say hello",
};

export function CallExperience() {
  const room = useRoomContext();
  const connection = useConnectionState();
  const { state } = useVoiceAssistant();
  const view = useMonitorEvents();

  const reconnecting = connection === ConnectionState.Reconnecting;
  const connected = connection === ConnectionState.Connected;
  const active = !reconnecting && (state === "speaking" || state === "listening");

  const statusText = reconnecting
    ? "Reconnecting… hold on a moment"
    : connected
      ? STATUS[state] ?? "Connected"
      : "Connecting…";

  return (
    <div className="call-stage wide">
      <RoomAudioRenderer />

      <div className="call-card card">
        <h2>You&apos;re on a call</h2>
        <p className="sub">{statusText}</p>

        <div className={`viz ${active ? "active" : ""} ${reconnecting ? "dim" : ""}`}>
          {Array.from({ length: 7 }).map((_, i) => (
            <span className="bar" key={i} />
          ))}
        </div>

        <button className="btn btn-danger" onClick={() => room.disconnect()}>
          End call
        </button>
      </div>

      <TranscriptFeed messages={view.messages} interimCaller={view.interimCaller} />
    </div>
  );
}
