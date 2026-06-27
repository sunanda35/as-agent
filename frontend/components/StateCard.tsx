import { AgentState } from "@/lib/types";

const COPY: Record<AgentState, { label: string; sub: string; cls: string }> = {
  initializing: { label: "Getting ready", sub: "Warming up the assistant", cls: "" },
  listening: { label: "Listening", sub: "Hearing the caller out", cls: "is-listening" },
  thinking: { label: "Thinking", sub: "Working out the next step", cls: "is-thinking" },
  speaking: { label: "Speaking", sub: "Replying to the caller", cls: "is-speaking" },
  idle: { label: "Idle", sub: "Waiting for the caller", cls: "" },
  away: { label: "Paused", sub: "Caller stepped away", cls: "" },
};

export function StateCard({
  state,
  ended,
}: {
  state: AgentState;
  ended?: boolean;
}) {
  const view = ended
    ? { label: "Call ended", sub: "The conversation is complete", cls: "" }
    : COPY[state] ?? COPY.idle;
  return (
    <div className={`statecard ${view.cls}`}>
      <div className="state-orb">
        <span className="ring" />
        <span className="core" />
      </div>
      <div>
        <div className="state-label">{view.label}</div>
        <div className="state-sub">{view.sub}</div>
      </div>
    </div>
  );
}
