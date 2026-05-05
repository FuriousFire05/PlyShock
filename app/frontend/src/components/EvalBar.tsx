import { Gauge } from "lucide-react";
import type { ReplayMove } from "@/types/plyshock";
import { clamp, formatEval } from "@/lib/utils";

interface EvalBarProps {
  move: ReplayMove | null;
}

export function EvalBar({ move }: EvalBarProps) {
  const rawBar = move?.stockfish_bar ?? 0;
  const bar = clamp(rawBar, -1, 1);
  const whiteWidth = `${(bar + 1) * 50}%`;
  const advantage =
    Math.abs(move?.stockfish_eval_cp_white_pov ?? 0) < 25
      ? "Equal"
      : (move?.stockfish_eval_cp_white_pov ?? 0) > 0
        ? "White advantage"
        : "Black advantage";

  return (
    <section className="panel border border-white/10 p-5">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <p className="font-mono text-[0.66rem] uppercase tracking-[0.22em] text-gold">
            Stockfish eval bar
          </p>
          <h2 className="mt-2 text-xl font-semibold text-ivory">{advantage}</h2>
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
        <span className="font-semibold text-ivory">
          {formatEval(move?.stockfish_eval_cp_white_pov)}
        </span>
      </div>
      <p className="mt-2 text-xs leading-5 text-stone-500">
        This engine signal updates every returned ply and is separate from PlyShock checkpoints.
      </p>
    </section>
  );
}
