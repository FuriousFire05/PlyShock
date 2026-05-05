import { Flag, Sparkles } from "lucide-react";
import type { ReplayMove } from "@/types/plyshock";
import { cn } from "@/lib/utils";

interface MoveListProps {
  moves: ReplayMove[];
  currentPly: number;
  onSelectPly: (ply: number) => void;
}

export function MoveList({ moves, currentPly, onSelectPly }: MoveListProps) {
  const playableMoves = moves.filter((move) => move.ply > 0);
  const pairs: Array<{ fullmove: number; white?: ReplayMove; black?: ReplayMove }> = [];

  for (const move of playableMoves) {
    let pair = pairs.find((item) => item.fullmove === move.fullmove);
    if (!pair) {
      pair = { fullmove: move.fullmove };
      pairs.push(pair);
    }
    if (move.ply % 2 === 1) {
      pair.white = move;
    } else {
      pair.black = move;
    }
  }

  return (
    <section className="panel border border-white/10 p-5">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <p className="font-mono text-[0.66rem] uppercase tracking-[0.22em] text-gold">
            Move list
          </p>
          <h2 className="mt-2 text-xl font-semibold text-ivory">PGN replay</h2>
        </div>
        <Flag className="text-gold" size={21} />
      </div>

      <div className="max-h-[460px] space-y-1 overflow-y-auto pr-1">
        <button
          type="button"
          onClick={() => onSelectPly(0)}
          className={cn(
            "grid w-full grid-cols-[42px_1fr_1fr] gap-2 rounded-xl border px-3 py-2 text-left text-sm transition",
            currentPly === 0
              ? "border-gold/45 bg-gold/12 text-ivory"
              : "border-white/5 bg-white/[0.02] text-stone-400 hover:border-white/15"
          )}
        >
          <span className="font-mono text-xs text-stone-500">0</span>
          <span>Starting position</span>
          <span />
        </button>

        {pairs.map((pair) => (
          <div
            key={pair.fullmove}
            className="grid grid-cols-[42px_1fr_1fr] gap-2 rounded-xl border border-white/5 bg-white/[0.02] px-3 py-2"
          >
            <div className="pt-1 font-mono text-xs text-stone-500">{pair.fullmove}.</div>
            <MoveButton move={pair.white} currentPly={currentPly} onSelectPly={onSelectPly} />
            <MoveButton move={pair.black} currentPly={currentPly} onSelectPly={onSelectPly} />
          </div>
        ))}
      </div>
    </section>
  );
}

function MoveButton({
  move,
  currentPly,
  onSelectPly,
}: {
  move?: ReplayMove;
  currentPly: number;
  onSelectPly: (ply: number) => void;
}) {
  if (!move) {
    return <span />;
  }

  const active = move.ply === currentPly;
  return (
    <button
      type="button"
      onClick={() => onSelectPly(move.ply)}
      className={cn(
        "flex min-w-0 items-center gap-1 rounded-lg px-2 py-1 text-left text-sm transition",
        active ? "bg-gold/18 text-ivory" : "text-stone-300 hover:bg-white/[0.05]",
        move.is_checkpoint && "ring-1 ring-gold/35"
      )}
      title={`Ply ${move.ply}${move.is_checkpoint ? " · PlyShock checkpoint" : ""}`}
    >
      {move.is_checkpoint ? <Sparkles className="shrink-0 text-gold" size={12} /> : null}
      <span className="truncate">{move.san}</span>
    </button>
  );
}
