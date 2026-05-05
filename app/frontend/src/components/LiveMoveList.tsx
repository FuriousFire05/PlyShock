import { ListChecks, Sparkles } from "lucide-react";
import type { LiveMoveRecord } from "@/types/plyshock";
import { cn } from "@/lib/utils";

interface LiveMoveListProps {
  moves: LiveMoveRecord[];
}

export function LiveMoveList({ moves }: LiveMoveListProps) {
  return (
    <section className="panel border border-white/10 p-5">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <p className="font-mono text-[0.66rem] uppercase tracking-[0.22em] text-gold">
            Live move history
          </p>
          <h2 className="mt-2 text-xl font-semibold text-ivory">{moves.length} plies</h2>
        </div>
        <ListChecks className="text-gold" size={21} />
      </div>

      <div className="max-h-[380px] space-y-1 overflow-y-auto pr-1">
        {moves.length === 0 ? (
          <p className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-sm text-stone-500">
            Legal moves will appear here.
          </p>
        ) : (
          moves.map((move) => (
            <div
              key={move.ply}
              className={cn(
                "grid grid-cols-[42px_58px_1fr] items-center gap-2 rounded-xl border px-3 py-2 text-sm",
                move.is_checkpoint
                  ? "border-gold/40 bg-gold/[0.08] text-ivory"
                  : "border-white/5 bg-white/[0.025] text-stone-300"
              )}
            >
              <span className="font-mono text-xs text-stone-500">{move.ply}</span>
              <span className="font-mono text-xs text-stone-500">M{move.fullmove}</span>
              <span className="flex min-w-0 items-center gap-2">
                {move.is_checkpoint ? <Sparkles className="shrink-0 text-gold" size={13} /> : null}
                <span className="truncate">{move.san}</span>
              </span>
            </div>
          ))
        )}
      </div>
    </section>
  );
}
