"use client";

import { LiveKitRoom } from "@livekit/components-react";
import { useState } from "react";
import { TopBar } from "@/components/TopBar";
import { CallView } from "@/components/CallView";
import { ConnectionDetails, fetchConnectionDetails } from "@/lib/connection";

export default function Home() {
  const [conn, setConn] = useState<ConnectionDetails | null>(null);
  const [connecting, setConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const start = async () => {
    setConnecting(true);
    setError(null);
    try {
      const room = `call-${Math.random().toString(36).slice(2, 10)}`;
      setConn(await fetchConnectionDetails("caller", room));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not start the call.");
    } finally {
      setConnecting(false);
    }
  };

  return (
    <main className="page">
      <TopBar />

      {!conn ? (
        <div className="call-stage">
          <div className="call-card card">
            <h2>Talk to the booking assistant</h2>
            <p className="sub">
              We&apos;ll ask for your microphone, then you can speak normally.
            </p>
            <div className="viz">
              {Array.from({ length: 7 }).map((_, i) => (
                <span className="bar" key={i} />
              ))}
            </div>
            <button className="btn btn-primary" onClick={start} disabled={connecting}>
              {connecting ? "Starting…" : "Start call"}
            </button>
            {error && <div className="error">{error}</div>}
            <p className="hint">
              Try “I&apos;d like to book a cleaning for tomorrow afternoon.”
            </p>
          </div>
        </div>
      ) : (
        <LiveKitRoom
          key={conn.room}
          serverUrl={conn.url}
          token={conn.token}
          connect
          audio
          video={false}
        >
          <CallView onRestart={start} />
        </LiveKitRoom>
      )}
    </main>
  );
}
