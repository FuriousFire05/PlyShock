import { AlertCircle, CheckCircle2, Target } from "lucide-react";
import type { ReplayCheckpoint, ReplayMove, ReplayMetadata, PlyShockPrediction } from "@/types/plyshock";
import { cn, formatClock, formatEval, formatPercent } from "@/lib/utils";

interface PlyShockBarProps {
  currentMove: ReplayMove | null;
  latestCheckpoint: ReplayCheckpoint | null;
  latestPrediction: PlyShockPrediction | null;
  metadata: ReplayMetadata | null;
}

export function PlyShockBar({
  currentMove,
  latestCheckpoint,
  latestPrediction,
  metadata,
}: PlyShockBarProps) {
  const beforeActivation = (currentMove?.ply ?? 0) < 30 || !latestPrediction || !latestCheckpoint;
  const probability = latestPrediction?.upset_probability ?? null;
  const upset = latestPrediction?.predicted_label === 1;

  return (
    <section className="panel border border-gold/15 p-5">
      <div className="mb-5 flex items-center justify-between gap-3">
        <div>
          <p className="font-mono text-[0.66rem] uppercase tracking-[0.22em] text-gold">
            PlyShock checkpoint
          </p>
          <h2 className="mt-2 text-xl font-semibold text-ivory">Upset probability estimate</h2>
        </div>
        <Target className="text-gold" size={23} />
      </div>

      {beforeActivation ? (
        <div className="rounded-3xl border border-white/10 bg-white/[0.035] p-5">
          <p className="text-lg font-semibold text-ivory">PlyShock activates at move 15</p>
          <p className="mt-2 text-sm leading-6 text-stone-400">
            Stockfish eval updates every move. PlyShock predictions update only at trained
            checkpoint moves 15, 20, 25, 30, and 35.
          </p>
        </div>
      ) : (
        <>
          <div
            className={cn(
              "rounded-3xl border p-5",
              upset ? "border-red-400/25 bg-red-400/[0.065]" : "border-green-400/25 bg-green-400/[0.065]"
            )}
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm text-stone-400">Latest checkpoint move</p>
                <p className="mt-1 text-4xl font-semibold text-ivory">
                  {latestCheckpoint?.snapshot_move}
                </p>
              </div>
              <div
                className={cn(
                  "rounded-2xl border p-3",
                  upset ? "border-red-300/25 text-red-300" : "border-green-300/25 text-green-300"
                )}
              >
                {upset ? <AlertCircle size={24} /> : <CheckCircle2 size={24} />}
              </div>
            </div>

            <div className="mt-5">
              <div className="mb-2 flex items-center justify-between">
                <span className="text-sm text-stone-400">Lower-rated win probability</span>
                <span className="text-lg font-semibold text-ivory">{formatPercent(probability)}</span>
              </div>
              <div className="h-3 overflow-hidden rounded-full bg-black/35">
                <div
                  className={cn("h-full rounded-full", upset ? "bg-red-300" : "bg-green-300")}
                  style={{ width: `${Math.max(0, Math.min(1, probability ?? 0)) * 100}%` }}
                />
              </div>
            </div>

            <p className="mt-4 text-sm font-semibold text-ivory">
              {upset ? "Predicted label: upset" : "Predicted label: non-upset"}
            </p>
            <p className="mt-1 text-xs leading-5 text-stone-400">{latestPrediction?.interpretation}</p>
          </div>

          <div className="mt-3 grid grid-cols-3 gap-2">
            <Mini label="Lower eval" value={formatEval(latestPrediction?.eval_cp_lower_pov)} />
            <Mini label="Lower clock" value={formatClock(latestPrediction?.lower_clock_sec)} />
            <Mini label="Higher clock" value={formatClock(latestPrediction?.higher_clock_sec)} />
          </div>
        </>
      )}

      <p className="mt-4 text-xs leading-5 text-stone-500">
        Upset means the lower-rated player beats the higher-rated player. In this game, the
        lower-rated player is {metadata?.lower_rated_color ?? "unknown"}.
      </p>
    </section>
  );
}

function Mini({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/[0.035] p-3">
      <p className="font-mono text-[0.6rem] uppercase tracking-[0.16em] text-stone-500">{label}</p>
      <p className="mt-1 text-sm font-semibold text-ivory">{value}</p>
    </div>
  );
}
