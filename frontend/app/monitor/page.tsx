"use client";

import { LiveKitRoom } from "@livekit/components-react";
import { useEffect, useRef, useState } from "react";
import { TopBar } from "@/components/TopBar";
import { Dashboard } from "@/components/Dashboard";
import { ConnectionDetails, fetchConnectionDetails } from "@/lib/connection";

const POLL_MS = 2000;

export default function MonitorPage() {
  const [conn, setConn] = useState<ConnectionDetails | null>(null);
  const [error, setError] = useState<string | null>(null);
  const connectedRoom = useRef<string | null>(null);

  useEffect(() => {
    let stop = false;

    const tick = async () => {
      try {
        const res = await fetch("/api/active-room", { cache: "no-store" });
        const { room } = await res.json();
        if (!stop && room && room !== connectedRoom.current) {
          connectedRoom.current = room;
          setConn(await fetchConnectionDetails("watcher", room));
        }
      } catch (e) {
        if (!stop) setError(e instanceof Error ? e.message : "Lost connection to server.");
      }
    };

    tick();
    const id = setInterval(tick, POLL_MS);
    return () => {
      stop = true;
      clearInterval(id);
    };
  }, []);

  return (
    <main className="page">
      <TopBar active="monitor" />
      {error && <div className="error">{error}</div>}
      {!conn ? (
        <div className="center">
          <div className="waiting-pulse" />
          Waiting for a call to start…
          <p className="hint" style={{ marginTop: 10 }}>
            Open the call page in another tab and start a call.
          </p>
        </div>
      ) : (
        <LiveKitRoom
          key={conn.room}
          serverUrl={conn.url}
          token={conn.token}
          connect
          audio={false}
          video={false}
        >
          <Dashboard />
        </LiveKitRoom>
      )}
    </main>
  );
}
