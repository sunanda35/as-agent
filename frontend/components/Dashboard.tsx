"use client";

import {
  RoomAudioRenderer,
  useConnectionState,
  useVoiceAssistant,
} from "@livekit/components-react";
import { ConnectionState } from "livekit-client";
import { useMonitorEvents } from "@/lib/useMonitorEvents";
import { AgentState } from "@/lib/types";
import { StateCard } from "./StateCard";
import { CallMeta } from "./CallMeta";
import { ActionCard } from "./ActionCard";
import { TranscriptFeed } from "./TranscriptFeed";

const KNOWN: AgentState[] = [
  "initializing",
  "listening",
  "thinking",
  "speaking",
  "idle",
  "away",
];

export function Dashboard() {
  const view = useMonitorEvents();
  const connection = useConnectionState();
  const { state: liveState, agent } = useVoiceAssistant();

  const connected = connection === ConnectionState.Connected;
  const ended = view.callStatus === "ended";
  const agentPresent = Boolean(agent);

  const agentState: AgentState = ended
    ? "idle"
    : KNOWN.includes(liveState as AgentState)
      ? (liveState as AgentState)
      : view.agentState;

  return (
    <>
      <RoomAudioRenderer />

      <div className="monitor-bar">
        <span className="status-row">
          <span className={`dot ${connected ? "live" : ""}`} />
          {connected ? "Live monitor connected" : "Connecting…"}
        </span>
        <span className="presence">
          <span className={`dot ${agentPresent ? "live" : "ended"}`} />
          {agentPresent ? "Assistant in room" : "Waiting for a call"}
        </span>
      </div>

      <div className="dashboard">
        <div className="stack">
          <div className="card panel">
            <p className="panel-title">Assistant state</p>
            <StateCard state={agentState} ended={ended} />
          </div>

          <div className="card panel">
            <p className="panel-title">Call</p>
            <CallMeta status={view.callStatus} />
          </div>

          <div className="card panel">
            <p className="panel-title">Current action</p>
            <ActionCard action={view.action} />
          </div>
        </div>

        <div>
          <TranscriptFeed
            messages={view.messages}
            interimCaller={view.interimCaller}
          />
          {view.summary && (
            <div className="summary-card">
              <h4>📝 Post-call summary</h4>
              <pre>{view.summary}</pre>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
