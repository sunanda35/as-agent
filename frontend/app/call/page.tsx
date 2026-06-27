"use client";

import { LiveKitRoom } from "@livekit/components-react";
import { useState } from "react";
import { TopBar } from "@/components/TopBar";
import { CallExperience } from "@/components/CallExperience";
import { ConnectionDetails, fetchConnectionDetails } from "@/lib/connection";

type Phase = "idle" | "live" | "ended";

export default function CallPage() {
  const [conn, setConn] = useState<ConnectionDetails | null>(null);
  const [phase, setPhase] = useState<Phase>("idle");
  const [connecting, setConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const start = async () => {
    setConnecting(true);
    setError(null);
    try {
      const room = `call-${Math.random().toString(36).slice(2, 10)}`;
      setConn(await fetchConnectionDetails("caller", room));
      setPhase("live");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not start the call.");
    } finally {
      setConnecting(false);
    }
  };

  return (
    <main className="page">
      <TopBar active="call" />

      {phase === "live" && conn ? (
        <LiveKitRoom
          serverUrl={conn.url}
          token={conn.token}
          connect
          audio
          video={false}
          onDisconnected={() => setPhase("ended")}
        >
          <CallExperience />
        </LiveKitRoom>
      ) : (
        <div className="call-stage">
          <div className="call-card card">
            {phase === "ended" ? (
              <>
                <h2>Call ended</h2>
                <p className="sub">Thanks for calling. Start another whenever you like.</p>
              </>
            ) : (
              <>
                <h2>Talk to the booking assistant</h2>
                <p className="sub">
                  We&apos;ll ask for your microphone, then you can speak normally.
                </p>
              </>
            )}

            <div className="viz">
              {Array.from({ length: 7 }).map((_, i) => (
                <span className="bar" key={i} />
              ))}
            </div>

            <button className="btn btn-primary" onClick={start} disabled={connecting}>
              {connecting ? "Starting…" : phase === "ended" ? "Start a new call" : "Start call"}
            </button>
            {error && <div className="error">{error}</div>}
            <p className="hint">
              Tip: open the live monitor in another tab to watch it work.
            </p>
          </div>
        </div>
      )}
    </main>
  );
}
