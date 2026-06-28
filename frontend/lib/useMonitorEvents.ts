"use client";

import { useDataChannel } from "@livekit/components-react";
import { useReducer } from "react";
import { MONITOR_TOPIC, MonitorEvent, MonitorView } from "./types";

const INITIAL: MonitorView = {
  agentState: "initializing",
  callStatus: "idle",
  messages: [],
  interimCaller: null,
  intent: null,
  action: null,
  summary: null,
  logs: [],
};

const MAX_LOGS = 120;
let seq = 0;
const nextId = () => `${Date.now()}-${seq++}`;

function withLog(state: MonitorView, entry: Omit<MonitorView["logs"][number], "id">): MonitorView["logs"] {
  const logs = [...state.logs, { id: nextId(), ...entry }];
  return logs.length > MAX_LOGS ? logs.slice(-MAX_LOGS) : logs;
}

function reduce(state: MonitorView, event: MonitorEvent): MonitorView {
  switch (event.kind) {
    case "state":
      return { ...state, agentState: event.state };

    case "call":
      return {
        ...state,
        callStatus: event.status,
        logs: withLog(state, {
          ts: event.ts,
          kind: "call",
          label: `Call ${event.status}`,
        }),
      };

    case "summary":
      return { ...state, summary: event.text };

    case "intent":
      return {
        ...state,
        intent: event.text,
        logs: withLog(state, {
          ts: event.ts,
          kind: "intent",
          label: "Intent detected",
          detail: event.text,
        }),
      };

    case "metric":
      return {
        ...state,
        logs: withLog(state, {
          ts: event.ts,
          kind: "metric",
          label: event.metric,
          detail: event.detail,
          ms: event.ms,
        }),
      };

    case "action":
      return {
        ...state,
        action: {
          label: event.label,
          status: event.status,
          detail: event.detail,
          ts: event.ts,
        },
        logs: withLog(state, {
          ts: event.ts,
          kind: "action",
          label: `${event.label} · ${event.status}`,
          detail: event.detail,
        }),
      };

    case "transcript": {
      if (event.role === "caller" && !event.final) {
        return { ...state, interimCaller: event.text };
      }
      if (!event.text.trim()) return state;
      return {
        ...state,
        interimCaller: event.role === "caller" ? null : state.interimCaller,
        messages: [
          ...state.messages,
          { id: nextId(), role: event.role, text: event.text, ts: event.ts },
        ],
      };
    }

    default:
      return state;
  }
}

export function useMonitorEvents(): MonitorView {
  const [view, dispatch] = useReducer(reduce, INITIAL);

  useDataChannel(MONITOR_TOPIC, (msg) => {
    try {
      const event = JSON.parse(new TextDecoder().decode(msg.payload)) as MonitorEvent;
      dispatch(event);
    } catch {
      // ignore malformed monitor frames
    }
  });

  return view;
}
