import {
  AccessToken,
  RoomAgentDispatch,
  RoomConfiguration,
} from "livekit-server-sdk";
import { NextRequest, NextResponse } from "next/server";

const AGENT_NAME = "booking-agent";

const ROLES = {
  caller: { canPublish: true, canSubscribe: true, dispatchAgent: true },
  watcher: { canPublish: true, canSubscribe: true, dispatchAgent: false },
} as const;

type Role = keyof typeof ROLES;

export async function GET(req: NextRequest) {
  const apiKey = process.env.LIVEKIT_API_KEY;
  const apiSecret = process.env.LIVEKIT_API_SECRET;
  const url = process.env.NEXT_PUBLIC_LIVEKIT_URL;

  if (!apiKey || !apiSecret || !url) {
    return NextResponse.json(
      { error: "Server is missing LiveKit credentials." },
      { status: 500 },
    );
  }

  const params = req.nextUrl.searchParams;
  const role = (params.get("role") ?? "caller") as Role;
  const room =
    params.get("room") ?? process.env.NEXT_PUBLIC_ROOM_NAME ?? "booking-room";

  if (!(role in ROLES)) {
    return NextResponse.json({ error: "Unknown role." }, { status: 400 });
  }

  const identity = `${role}-${Math.random().toString(36).slice(2, 8)}`;
  const grant = ROLES[role];

  const at = new AccessToken(apiKey, apiSecret, {
    identity,
    name: role === "caller" ? "Caller" : "Watcher",
    ttl: "1h",
  });
  at.addGrant({
    roomJoin: true,
    room,
    canPublish: grant.canPublish,
    canSubscribe: grant.canSubscribe,
    canPublishData: true,
  });

  if (grant.dispatchAgent) {
    at.roomConfig = new RoomConfiguration({
      agents: [new RoomAgentDispatch({ agentName: AGENT_NAME })],
    });
  }

  const token = await at.toJwt();
  return NextResponse.json({ token, url, identity, room, role });
}
