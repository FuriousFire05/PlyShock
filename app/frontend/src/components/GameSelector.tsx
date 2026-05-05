import { ChevronDown, Database } from "lucide-react";
import type { DemoGame } from "@/types/plyshock";

interface GameSelectorProps {
  games: DemoGame[];
  selectedId: string | null;
  loading: boolean;
  disabled?: boolean;
  onSelect: (gameId: string) => void;
}

export function GameSelector({ games, selectedId, loading, disabled, onSelect }: GameSelectorProps) {
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
              {game.filename}
            </option>
          ))}
        </select>
        <ChevronDown
          className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-stone-500"
          size={18}
        />
      </label>

      <p className="mt-4 text-xs leading-5 text-stone-500">
        Replays use move-by-move Stockfish evals. PlyShock predictions appear only at trained
        checkpoints.
      </p>
    </section>
  );
}
