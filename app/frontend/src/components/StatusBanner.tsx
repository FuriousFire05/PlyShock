import { CheckCircle2, Server, WifiOff } from "lucide-react";
import type { BackendHealth } from "@/types/plyshock";
import { API_BASE_URL } from "@/lib/api";
import { cn } from "@/lib/utils";

interface StatusBannerProps {
  health: BackendHealth | null;
  loading: boolean;
  error: string | null;
}

export function StatusBanner({ health, loading, error }: StatusBannerProps) {
  const online = Boolean(health && !error);
  const Icon = loading ? Server : online ? CheckCircle2 : WifiOff;

  return (
    <div
      className={cn(
        "panel flex flex-col gap-3 border p-4 md:flex-row md:items-center md:justify-between",
        online ? "border-green-400/25 bg-green-400/[0.05]" : "border-red-400/25 bg-red-400/[0.05]"
      )}
    >
      <div className="flex items-center gap-3">
        <div
          className={cn(
            "rounded-xl border p-2",
            online ? "border-green-400/30 text-green-300" : "border-red-400/30 text-red-300"
          )}
        >
          <Icon size={18} />
        </div>
        <div>
          <p className="text-sm font-semibold text-ivory">
            {loading ? "Checking backend" : online ? "Backend online" : "Backend offline"}
          </p>
          <p className="text-xs leading-5 text-stone-400">
            {error ??
              `${API_BASE_URL} · ${health?.demo_games_count ?? 0} demo games · Stockfish ${
                health?.stockfish_exists ? "ready" : "unavailable"
              }`}
          </p>
        </div>
      </div>
      {!online && !loading ? (
        <p className="rounded-lg border border-red-400/20 bg-black/25 px-3 py-2 text-xs text-red-200">
          Start FastAPI at http://127.0.0.1:8000, then refresh.
        </p>
      ) : null}
    </div>
  );
}
