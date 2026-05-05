import { Target } from "lucide-react";
import type { ReplayCheckpoint } from "@/types/plyshock";
import { cn, formatPercent } from "@/lib/utils";

interface CheckpointTimelineProps {
  checkpoints: ReplayCheckpoint[];
  currentPly: number;
  onSelectPly: (ply: number) => void;
}

export function CheckpointTimeline({
  checkpoints,
  currentPly,
  onSelectPly,
}: CheckpointTimelineProps) {
  const moves = [15, 20, 25, 30, 35];
  const byMove = new Map(checkpoints.map((checkpoint) => [checkpoint.snapshot_move, checkpoint]));

  return (
    <section className="panel border border-white/10 p-5">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <p className="font-mono text-[0.66rem] uppercase tracking-[0.22em] text-gold">
            Checkpoint timeline
          </p>
          <h2 className="mt-2 text-xl font-semibold text-ivory">PlyShock updates</h2>
        </div>
        <Target className="text-gold" size={21} />
      </div>

      <div className="grid grid-cols-5 gap-2">
        {moves.map((moveNumber) => {
          const checkpoint = byMove.get(moveNumber);
          const active = checkpoint ? currentPly >= checkpoint.ply : false;
          return (
            <button
              key={moveNumber}
              type="button"
              disabled={!checkpoint}
              onClick={() => checkpoint && onSelectPly(checkpoint.ply)}
              className={cn(
                "rounded-2xl border p-3 text-left transition",
                active
                  ? "border-gold/55 bg-gold/15 text-ivory"
                  : "border-white/10 bg-white/[0.03] text-stone-400 hover:border-gold/35",
                !checkpoint && "cursor-not-allowed opacity-35"
              )}
            >
              <span className="font-mono text-[0.62rem] uppercase tracking-[0.16em]">
                M{moveNumber}
              </span>
              <span className="mt-2 block text-sm font-semibold">
                {checkpoint ? formatPercent(checkpoint.upset_probability, 0) : "--"}
              </span>
              <span className="mt-1 block text-[0.68rem] text-stone-500">
                {checkpoint ? `ply ${checkpoint.ply}` : "missing"}
              </span>
            </button>
          );
        })}
      </div>

      <p className="mt-4 text-xs leading-5 text-stone-500">
        These are the only positions where the trained PlyShock model is queried.
      </p>
    </section>
  );
}
