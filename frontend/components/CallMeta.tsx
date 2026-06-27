"use client";

import { useEffect, useRef, useState } from "react";
import { CallStatus } from "@/lib/types";

const LABEL: Record<CallStatus, string> = {
  idle: "Waiting for call",
  live: "Live",
  ended: "Call ended",
};

function format(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export function CallMeta({ status }: { status: CallStatus }) {
  const [elapsed, setElapsed] = useState(0);
  const startRef = useRef<number | null>(null);

  useEffect(() => {
    if (status === "live" && startRef.current === null) {
      startRef.current = Date.now();
    }
    if (status !== "live") return;

    const id = setInterval(() => {
      if (startRef.current !== null) {
        setElapsed(Math.floor((Date.now() - startRef.current) / 1000));
      }
    }, 1000);
    return () => clearInterval(id);
  }, [status]);

  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
      <div className="status-row">
        <span className={`dot ${status}`} />
        {LABEL[status]}
      </div>
      {startRef.current !== null && <span className="timer">{format(elapsed)}</span>}
    </div>
  );
}
