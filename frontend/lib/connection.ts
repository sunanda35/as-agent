export interface ConnectionDetails {
  token: string;
  url: string;
  identity: string;
  room: string;
  role: "caller" | "watcher";
}

export async function fetchConnectionDetails(
  role: "caller" | "watcher",
  room?: string,
): Promise<ConnectionDetails> {
  const params = new URLSearchParams({ role });
  if (room) params.set("room", room);

  const res = await fetch(`/api/token?${params.toString()}`, { cache: "no-store" });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error ?? "Could not get a connection token.");
  }
  return res.json();
}
