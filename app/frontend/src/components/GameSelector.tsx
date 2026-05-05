import { ChevronDown, Database } from "lucide-react";
import type { DemoGame } from "@/types/plyshock";
import { cn } from "@/lib/utils";

interface GameSelectorProps {
  games: DemoGame[];
  selectedId: string | null;
  loading: boolean;
  disabled?: boolean;
  onSelect: (gameId: string) => void;
}

export function GameSelector({ games, selectedId, loading, disabled, onSelect }: GameSelectorProps) {
  const selectedGame = games.find((game) => game.id === selectedId) ?? null;

  return (
    <section className="panel border border-white/10 p-5">
      <div className="mb-4 flex items-center justify-between gap-4">
        <div>
          <p className="font-mono text-[0.66rem] uppercase tracking-[0.22em] text-gold">
            Demo PGNs
          </p>
          <h2 className="mt-2 text-xl font-semibold text-ivory">Select a replay</h2>
        </div>
        <Database className="text-gold" size={22} />
      </div>

      <label className="relative block">
        <select
          value={selectedId ?? ""}
          disabled={disabled || loading || games.length === 0}
          onChange={(event) => onSelect(event.target.value)}
          className="h-12 w-full appearance-none rounded-xl border border-white/10 bg-black/35 px-4 pr-11 text-sm text-ivory outline-none transition focus:border-gold/60 focus:ring-2 focus:ring-gold/15 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <option value="" disabled>
            {loading ? "Loading games..." : games.length ? "Choose a demo game" : "No games found"}
          </option>
          {games.map((game) => (
            <option key={game.id} value={game.id}>
              {formatGameLabel(game)}
            </option>
          ))}
        </select>
        <ChevronDown
          className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-stone-500"
          size={18}
        />
      </label>

      {selectedGame ? (
        <div className="mt-4 grid gap-2 rounded-2xl border border-white/10 bg-white/[0.035] p-3">
          <div className="flex items-center justify-between gap-3">
            <p className="truncate text-sm font-semibold text-ivory">{formatGameLabel(selectedGame)}</p>
            <UpsetBadge value={selectedGame.actual_upset_label} />
          </div>
          <div className="grid grid-cols-3 gap-2 text-xs text-stone-400">
            <Mini label="Gap" value={formatOptional(selectedGame.rating_gap, "pts")} />
            <Mini label="Result" value={selectedGame.result ?? "--"} />
            <Mini label="Lower" value={selectedGame.lower_rated_color ?? "--"} />
          </div>
        </div>
      ) : null}

      <p className="mt-4 text-xs leading-5 text-stone-500">
        Replays use move-by-move Stockfish evals. PlyShock predictions appear only at trained
        checkpoints.
      </p>
    </section>
  );
}

function formatGameLabel(game: DemoGame) {
  if (game.label) {
    return game.label;
  }
  const white = game.white_elo ? `W${game.white_elo}` : null;
  const black = game.black_elo ? `B${game.black_elo}` : null;
  const ratings = white && black ? ` (${white} vs ${black})` : "";
  return `${game.filename}${ratings}`;
}

function formatOptional(value: number | null | undefined, suffix = "") {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "--";
  }
  return suffix ? `${value} ${suffix}` : String(value);
}

function Mini({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-white/5 bg-black/20 p-2">
      <p className="font-mono text-[0.58rem] uppercase tracking-[0.14em] text-stone-600">{label}</p>
      <p className="mt-1 truncate font-semibold text-stone-300">{value}</p>
    </div>
  );
}

function UpsetBadge({ value }: { value: number | null | undefined }) {
  const known = value === 0 || value === 1;
  return (
    <span
      className={cn(
        "shrink-0 rounded-full border px-2.5 py-1 text-[0.66rem] font-semibold uppercase tracking-[0.12em]",
        value === 1
          ? "border-red-300/30 bg-red-400/[0.08] text-red-200"
          : value === 0
            ? "border-green-300/30 bg-green-400/[0.08] text-green-200"
            : "border-white/10 bg-white/[0.04] text-stone-400"
      )}
    >
      {known ? (value === 1 ? "Upset" : "Non-upset") : "Demo"}
    </span>
  );
}
