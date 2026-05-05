import type { BackendHealth, DemoGame, ReplayResponse } from "@/types/plyshock";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "http://127.0.0.1:8000";

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    let message = `${response.status} ${response.statusText}`;
    try {
      const body = (await response.json()) as { detail?: unknown };
      if (typeof body.detail === "string") {
        message = body.detail;
      }
    } catch {
      // Keep the HTTP status text if the backend did not return JSON.
    }
    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

export const api = {
  health: () => fetchJson<BackendHealth>("/health"),
  demoGames: () => fetchJson<DemoGame[]>("/demo-games"),
  replay: (gameId: string) =>
    fetchJson<ReplayResponse>(`/demo-games/${encodeURIComponent(gameId)}/replay`),
};
