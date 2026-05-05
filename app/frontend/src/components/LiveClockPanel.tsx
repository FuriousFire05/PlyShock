import { Pause, Play, Timer, Trophy } from "lucide-react";
import type { PlayerColor } from "@/types/plyshock";
import { cn, formatClock } from "@/lib/utils";

interface LiveClockPanelProps {
  whiteClock: number;
  blackClock: number;
  activeColor: PlayerColor;
  running: boolean;
  paused: boolean;
  timedOutColor: PlayerColor | null;
  onTogglePause: () => void;
}

export function LiveClockPanel({
  whiteClock,
  blackClock,
  activeColor,
  running,
  paused,
  timedOutColor,
  onTogglePause,
}: LiveClockPanelProps) {
  return (
    <section className="panel border border-white/10 p-5">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <p className="font-mono text-[0.66rem] uppercase tracking-[0.22em] text-gold">
            Live clocks
          </p>
          <h2 className="mt-2 text-xl font-semibold text-ivory">
            {timedOutColor ? `${timedOutColor} flagged` : paused ? "Paused" : "Running"}
          </h2>
        </div>
        <Timer className="text-gold" size={22} />
      </div>

      <div className="grid gap-3">
        <ClockCard label="White" value={whiteClock} active={activeColor === "white" && running && !paused} />
        <ClockCard label="Black" value={blackClock} active={activeColor === "black" && running && !paused} dark />
      </div>

      <button
        type="button"
        onClick={onTogglePause}
        disabled={!running || Boolean(timedOutColor)}
        className="mt-4 inline-flex h-11 w-full items-center justify-center gap-2 rounded-xl border border-white/10 bg-white/[0.04] text-sm font-semibold text-stone-300 transition hover:border-gold/35 hover:text-gold disabled:cursor-not-allowed disabled:opacity-40"
      >
        {paused ? <Play size={16} /> : <Pause size={16} />}
        {paused ? "Resume" : "Pause"}
      </button>

      {timedOutColor ? (
        <div className="mt-3 flex items-center gap-2 rounded-xl border border-red-400/25 bg-red-400/[0.07] px-3 py-2 text-sm text-red-200">
          <Trophy size={15} />
          {timedOutColor === "white" ? "Black" : "White"} wins on time.
        </div>
      ) : null}
    </section>
  );
}

function ClockCard({
  label,
  value,
  active,
  dark,
}: {
  label: string;
  value: number;
  active: boolean;
  dark?: boolean;
}) {
  return (
    <div
      className={cn(
        "rounded-2xl border p-4",
        active ? "border-gold/55 bg-gold/12" : "border-white/10 bg-white/[0.035]"
      )}
    >
      <p className="font-mono text-[0.62rem] uppercase tracking-[0.18em] text-stone-500">
        {label}
      </p>
      <div className="mt-2 flex items-center justify-between">
        <p className={cn("text-3xl font-semibold", dark ? "text-stone-200" : "text-ivory")}>
          {formatClock(value)}
        </p>
        {active ? <span className="h-2.5 w-2.5 rounded-full bg-gold shadow-[0_0_18px_rgba(212,175,55,0.8)]" /> : null}
      </div>
    </div>
  );
}
