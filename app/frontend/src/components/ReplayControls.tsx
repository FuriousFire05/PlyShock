import { Pause, Play, SkipBack, SkipForward, StepBack, StepForward } from "lucide-react";

interface ReplayControlsProps {
  currentIndex: number;
  maxIndex: number;
  isPlaying: boolean;
  onFirst: () => void;
  onPrevious: () => void;
  onNext: () => void;
  onLast: () => void;
  onTogglePlay: () => void;
  onSeek: (index: number) => void;
}

export function ReplayControls({
  currentIndex,
  maxIndex,
  isPlaying,
  onFirst,
  onPrevious,
  onNext,
  onLast,
  onTogglePlay,
  onSeek,
}: ReplayControlsProps) {
  return (
    <section className="panel border border-white/10 p-4">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <p className="font-mono text-[0.66rem] uppercase tracking-[0.22em] text-gold">
            Move controls
          </p>
          <p className="mt-1 text-sm text-stone-400">
            Ply {currentIndex} of {maxIndex}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <ControlButton label="First" onClick={onFirst} disabled={currentIndex <= 0}>
            <SkipBack size={17} />
          </ControlButton>
          <ControlButton label="Previous" onClick={onPrevious} disabled={currentIndex <= 0}>
            <StepBack size={17} />
          </ControlButton>
          <ControlButton label={isPlaying ? "Pause" : "Play"} onClick={onTogglePlay} primary>
            {isPlaying ? <Pause size={18} /> : <Play size={18} />}
          </ControlButton>
          <ControlButton label="Next" onClick={onNext} disabled={currentIndex >= maxIndex}>
            <StepForward size={17} />
          </ControlButton>
          <ControlButton label="Last" onClick={onLast} disabled={currentIndex >= maxIndex}>
            <SkipForward size={17} />
          </ControlButton>
        </div>
      </div>

      <input
        aria-label="Replay ply"
        type="range"
        min={0}
        max={maxIndex}
        value={currentIndex}
        onChange={(event) => onSeek(Number(event.target.value))}
        className="replay-slider w-full"
      />
    </section>
  );
}

function ControlButton({
  label,
  children,
  disabled,
  primary,
  onClick,
}: {
  label: string;
  children: React.ReactNode;
  disabled?: boolean;
  primary?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      disabled={disabled}
      onClick={onClick}
      className={
        primary
          ? "grid h-10 w-10 place-items-center rounded-xl border border-gold/40 bg-gold/15 text-gold transition hover:bg-gold/20 disabled:cursor-not-allowed disabled:opacity-40"
          : "grid h-10 w-10 place-items-center rounded-xl border border-white/10 bg-white/[0.04] text-stone-300 transition hover:border-gold/35 hover:text-gold disabled:cursor-not-allowed disabled:opacity-35"
      }
    >
      {children}
    </button>
  );
}
