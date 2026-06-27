export const MONITOR_TOPIC = "agent-monitor";

export type AgentState =
  | "initializing"
  | "listening"
  | "thinking"
  | "speaking"
  | "idle"
  | "away";

export type CallStatus = "idle" | "live" | "ended";

export type ActionStatus = "running" | "done" | "failed";

export type MonitorEvent =
  | { kind: "state"; state: AgentState; ts: string }
  | { kind: "transcript"; role: "caller" | "agent"; text: string; final: boolean; ts: string }
  | { kind: "action"; label: string; status: ActionStatus; detail?: string | null; ts: string }
  | { kind: "call"; status: CallStatus; ts: string }
  | { kind: "summary"; text: string; ts: string };

export interface TranscriptMessage {
  id: string;
  role: "caller" | "agent";
  text: string;
  ts: string;
}

export interface ActionView {
  label: string;
  status: ActionStatus;
  detail?: string | null;
  ts: string;
}

export interface MonitorView {
  agentState: AgentState;
  callStatus: CallStatus;
  messages: TranscriptMessage[];
  interimCaller: string | null;
  action: ActionView | null;
  summary: string | null;
}
