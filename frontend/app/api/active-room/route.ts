import { RoomServiceClient } from "livekit-server-sdk";
import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

const CALL_ROOM_PREFIX = "call-";

function httpUrl(wsUrl: string): string {
  return wsUrl.replace(/^ws/, "http");
}

export async function GET() {
  const apiKey = process.env.LIVEKIT_API_KEY;
  const apiSecret = process.env.LIVEKIT_API_SECRET;
  const wsUrl = process.env.NEXT_PUBLIC_LIVEKIT_URL;

  if (!apiKey || !apiSecret || !wsUrl) {
    return NextResponse.json({ error: "Missing LiveKit credentials." }, { status: 500 });
  }

  const svc = new RoomServiceClient(httpUrl(wsUrl), apiKey, apiSecret);

  try {
    const rooms = await svc.listRooms();
    const active = rooms
      .filter((r) => r.name.startsWith(CALL_ROOM_PREFIX) && r.numParticipants > 0)
      .sort((a, b) => Number(b.creationTime) - Number(a.creationTime));

    return NextResponse.json({ room: active[0]?.name ?? null });
  } catch {
    return NextResponse.json({ room: null });
  }
}
