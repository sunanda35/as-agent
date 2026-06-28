"use client";

import {
  RoomAudioRenderer,
  useConnectionState,
  useRoomContext,
  useVoiceAssistant,
} from "@livekit/components-react";
import { ConnectionState } from "livekit-client";
import { useEffect, useState } from "react";
import { useMonitorEvents } from "@/lib/useMonitorEvents";
import { AgentState, CallStatus } from "@/lib/types";
import { StateCard } from "./StateCard";
import { CallMeta } from "./CallMeta";
import { IntentCard } from "./IntentCard";
import { ActionCard } from "./ActionCard";
import { TranscriptFeed } from "./TranscriptFeed";
import { LogSidebar } from "./LogSidebar";

const KNOWN: AgentState[] = [
  "initializing",
  "listening",
  "thinking",
  "speaking",
  "idle",
  "away",
];

const CONTROL_TOPIC = "call-control";

export function CallView({ onRestart }: { onRestart: () => void }) {
  const room = useRoomContext();
  const connection = useConnectionState();
  const { state: liveState } = useVoiceAssistant();
  const view = useMonitorEvents();
  const [ending, setEnding] = useState(false);

  const reconnecting = connection === ConnectionState.Reconnecting;
  const disconnected = connection === ConnectionState.Disconnected;
  const ended = view.callStatus === "ended" || disconnected;

  useEffect(() => {
    if (view.callStatus === "ended" && connection === ConnectionState.Connected) {
      room.disconnect();
    }
  }, [view.callStatus, connection, room]);

  const requestEnd = async () => {
    setEnding(true);
    try {
      const payload = new TextEncoder().encode(JSON.stringify({ action: "end" }));
      await room.localParticipant.publishData(payload, {
        reliable: true,
        topic: CONTROL_TOPIC,
      });
    } catch {
      room.disconnect();
    }
  };

  if (ended) {
    return (
      <div className="call-stage wide">
        <RoomAudioRenderer />
        <div className="call-card card">
          <h2>Call ended</h2>
          <p className="sub">Thanks for calling Bright Smile.</p>
          <button className="btn btn-primary" onClick={onRestart}>
            Start a new call
          </button>
        </div>

        <div className="summary-card">
          <h4>📝 Call summary</h4>
          {view.summary ? (
            <pre>{view.summary}</pre>
          ) : (
            <p className="empty">No summary was generated for this call.</p>
          )}
        </div>

        <div className="ended-grid">
          {view.messages.length > 0 && (
            <TranscriptFeed messages={view.messages} interimCaller={null} />
          )}
          <LogSidebar logs={view.logs} />
        </div>
      </div>
    );
  }

  const transferring = view.callStatus === "transferring";

  const callStatus: CallStatus = transferring
    ? "transferring"
    : connection === ConnectionState.Connected
      ? "connected"
      : "connecting";

  const agentState: AgentState = KNOWN.includes(liveState as AgentState)
    ? (liveState as AgentState)
    : view.agentState;

  const active =
    !reconnecting && (agentState === "speaking" || agentState === "listening");

  return (
    <>
      <RoomAudioRenderer />

      {transferring && (
        <div className="transfer-banner">
          🔄 Connecting you to a teammate — please stay on the line.
        </div>
      )}

      <div className="dashboard with-logs">
        <div className="stack">
          <div className="card panel">
            <p className="panel-title">Call status</p>
            <CallMeta status={callStatus} />
          </div>

          <div className="card panel">
            <p className="panel-title">Assistant</p>
            <StateCard state={reconnecting ? "initializing" : agentState} />
            <div className={`viz small ${active ? "active" : ""} ${reconnecting ? "dim" : ""}`}>
              {Array.from({ length: 7 }).map((_, i) => (
                <span className="bar" key={i} />
              ))}
            </div>
          </div>

          <div className="card panel">
            <p className="panel-title">Detected intent</p>
            <IntentCard intent={view.intent} />
          </div>

          <div className="card panel">
            <p className="panel-title">Current action</p>
            <ActionCard action={view.action} />
          </div>

          <button
            className="btn btn-danger block"
            onClick={requestEnd}
            disabled={ending}
          >
            {ending ? "Wrapping up…" : "End call"}
          </button>
        </div>

        <TranscriptFeed messages={view.messages} interimCaller={view.interimCaller} />

        <LogSidebar logs={view.logs} />
      </div>
    </>
  );
}
