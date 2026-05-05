import { AlertCircle, CheckCircle2, Gauge, Target } from "lucide-react";
import type { LiveEvaluateResponse } from "@/types/plyshock";
import { clamp, cn, formatClock, formatEval, formatPercent } from "@/lib/utils";

interface LiveEvalPanelProps {
  evaluation: LiveEvaluateResponse | null;
  latestCheckpoint: LiveEvaluateResponse | null;
  evaluating: boolean;
  currentPly: number;
  error: string | null;
}

export function LiveEvalPanel({
  evaluation,
  latestCheckpoint,
  evaluating,
  currentPly,
  error,
}: LiveEvalPanelProps) {
  const rawBar = evaluation?.stockfish_bar ?? 0;
  const bar = clamp(rawBar, -1, 1);
  const whiteWidth = `${(bar + 1) * 50}%`;
  const evalCp = evaluation?.stockfish_eval_cp_white_pov ?? null;
  const advantage =
    Math.abs(evalCp ?? 0) < 25 ? "Equal" : (evalCp ?? 0) > 0 ? "White advantage" : "Black advantage";
  const checkpointPrediction = latestCheckpoint?.plyshock ?? null;
  const beforeActivation = currentPly < 30 || !checkpointPrediction;
  const isLatest = latestCheckpoint && !evaluation?.plyshock;

  return (
    <section className="space-y-6">
      <div className="panel border border-white/10 p-5">
        <div className="mb-4 flex items-center justify-between gap-3">
          <div>
            <p className="font-mono text-[0.66rem] uppercase tracking-[0.22em] text-gold">
              Live Stockfish eval
            </p>
            <h2 className="mt-2 text-xl font-semibold text-ivory">
              {evaluating ? "Evaluating..." : advantage}
            </h2>
          </div>
          <Gauge className="text-gold" size={22} />
        </div>

        <div className="overflow-hidden rounded-2xl border border-white/10 bg-black/35">
          <div className="relative h-12">
            <div className="absolute inset-0 bg-[#201b17]" />
            <div className="absolute inset-y-0 left-0 bg-[#e8dcc2]" style={{ width: whiteWidth }} />
            <div className="absolute inset-y-0 left-1/2 w-px bg-gold/70" />
            <div className="absolute inset-0 flex items-center justify-between px-4 font-mono text-xs">
              <span className="text-black/70">White</span>
              <span className="text-ivory/80">Black</span>
            </div>
          </div>
        </div>
        <div className="mt-3 flex items-center justify-between text-sm">
          <span className="text-stone-400">White POV</span>
          <span className="font-semibold text-ivory">{formatEval(evalCp)}</span>
        </div>
        {error ? <p className="mt-3 text-sm text-red-300">{error}</p> : null}
      </div>

      <div className="panel border border-gold/15 p-5">
        <div className="mb-5 flex items-center justify-between gap-3">
          <div>
            <p className="font-mono text-[0.66rem] uppercase tracking-[0.22em] text-gold">
              Live PlyShock
            </p>
            <h2 className="mt-2 text-xl font-semibold text-ivory">Upset probability estimate</h2>
          </div>
          <Target className="text-gold" size={23} />
        </div>

        {beforeActivation ? (
          <div className="rounded-3xl border border-white/10 bg-white/[0.035] p-5">
            <p className="text-lg font-semibold text-ivory">PlyShock activates at move 15</p>
            <p className="mt-2 text-sm leading-6 text-stone-400">
              Live mode uses Stockfish every move; PlyShock predictions are only produced at
              trained mid-game checkpoints.
            </p>
          </div>
        ) : (
          <div
            className={cn(
              "rounded-3xl border p-5",
              checkpointPrediction.predicted_label === 1
                ? "border-red-400/25 bg-red-400/[0.065]"
                : "border-green-400/25 bg-green-400/[0.065]"
            )}
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm text-stone-400">
                  {isLatest ? "Latest checkpoint prediction" : "Current checkpoint prediction"}
                </p>
                <p className="mt-1 text-4xl font-semibold text-ivory">
                  M{latestCheckpoint?.checkpoint_move}
                </p>
              </div>
              <div
                className={cn(
                  "rounded-2xl border p-3",
                  checkpointPrediction.predicted_label === 1
                    ? "border-red-300/25 text-red-300"
                    : "border-green-300/25 text-green-300"
                )}
              >
                {checkpointPrediction.predicted_label === 1 ? (
                  <AlertCircle size={24} />
                ) : (
                  <CheckCircle2 size={24} />
                )}
              </div>
            </div>

            <div className="mt-5">
              <div className="mb-2 flex items-center justify-between">
                <span className="text-sm text-stone-400">Lower-rated win probability</span>
                <span className="text-lg font-semibold text-ivory">
                  {formatPercent(checkpointPrediction.upset_probability)}
                </span>
              </div>
              <div className="h-3 overflow-hidden rounded-full bg-black/35">
                <div
                  className={cn(
                    "h-full rounded-full",
                    checkpointPrediction.predicted_label === 1 ? "bg-red-300" : "bg-green-300"
                  )}
                  style={{
                    width: `${Math.max(
                      0,
                      Math.min(1, checkpointPrediction.upset_probability ?? 0)
                    ) * 100}%`,
                  }}
                />
              </div>
            </div>

            <p className="mt-4 text-sm font-semibold text-ivory">
              {checkpointPrediction.predicted_label === 1
                ? "Predicted label: upset"
                : "Predicted label: non-upset"}
            </p>
            <p className="mt-1 text-xs leading-5 text-stone-400">
              {checkpointPrediction.interpretation}
            </p>
            <div className="mt-3 grid grid-cols-2 gap-2">
              <Mini label="Lower clock" value={formatClock(latestCheckpoint?.lower_clock_sec)} />
              <Mini label="Higher clock" value={formatClock(latestCheckpoint?.higher_clock_sec)} />
            </div>
          </div>
        )}
      </div>
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
