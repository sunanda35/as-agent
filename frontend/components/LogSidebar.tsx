"use client";

import { useEffect, useRef } from "react";
import { LogEntry } from "@/lib/types";

const ICON: Record<string, string> = {
  metric: "⚡",
  action: "🛠️",
  intent: "🎯",
  call: "📞",
};

function clock(ts: string): string {
  const d = new Date(ts);
  return d.toLocaleTimeString([], { hour12: false });
}

function msClass(ms: number): string {
  if (ms < 500) return "good";
  if (ms < 1200) return "ok";
  return "slow";
}

export function LogSidebar({ logs }: { logs: LogEntry[] }) {
  const endRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs.length]);

  return (
    <div className="card panel logbar">
      <p className="panel-title">Activity &amp; latency</p>
      <div className="log-scroll">
        {logs.length === 0 && (
          <div className="empty">Model calls and actions will appear here.</div>
        )}
        {logs.map((e) => (
          <div className="log-row" key={e.id}>
            <span className="log-icon">{ICON[e.kind] ?? "•"}</span>
            <div className="log-body">
              <div className="log-line">
                <span className="log-label">{e.label}</span>
                {typeof e.ms === "number" && (
                  <span className={`log-ms ${msClass(e.ms)}`}>{e.ms} ms</span>
                )}
              </div>
              {e.detail && <div className="log-detail">{e.detail}</div>}
            </div>
            <span className="log-time">{clock(e.ts)}</span>
          </div>
        ))}
        <div ref={endRef} />
      </div>
    </div>
  );
}
