import { RotateCcw, Rocket } from "lucide-react";

export interface LiveSetupValues {
  whiteElo: number;
  blackElo: number;
  initialMinutes: number;
  incrementSeconds: number;
}

interface LiveSetupPanelProps {
  values: LiveSetupValues;
  running: boolean;
  evaluating: boolean;
  onChange: (values: LiveSetupValues) => void;
  onStart: () => void;
  onReset: () => void;
}

export function LiveSetupPanel({
  values,
  running,
  evaluating,
  onChange,
  onStart,
  onReset,
}: LiveSetupPanelProps) {
  return (
    <section className="panel border border-white/10 p-5">
      <div className="mb-4">
        <p className="font-mono text-[0.66rem] uppercase tracking-[0.22em] text-gold">
          Live setup
        </p>
        <h2 className="mt-2 text-xl font-semibold text-ivory">Play a fresh board</h2>
      </div>

      <div className="grid gap-3">
        <NumberField
          label="White Elo"
          value={values.whiteElo}
          min={1}
          onChange={(whiteElo) => onChange({ ...values, whiteElo })}
        />
        <NumberField
          label="Black Elo"
          value={values.blackElo}
          min={1}
          onChange={(blackElo) => onChange({ ...values, blackElo })}
        />
        <NumberField
          label="Initial time (minutes)"
          value={values.initialMinutes}
          min={1}
          onChange={(initialMinutes) => onChange({ ...values, initialMinutes })}
        />
        <NumberField
          label="Increment (seconds)"
          value={values.incrementSeconds}
          min={0}
          onChange={(incrementSeconds) => onChange({ ...values, incrementSeconds })}
        />
      </div>

      <div className="mt-5 grid grid-cols-2 gap-3">
        <button
          type="button"
          onClick={onStart}
          disabled={evaluating}
          className="inline-flex h-11 items-center justify-center gap-2 rounded-xl border border-gold/40 bg-gold/15 px-4 text-sm font-semibold text-gold transition hover:bg-gold/20 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <Rocket size={16} />
          {running ? "Restart" : "Start game"}
        </button>
        <button
          type="button"
          onClick={onReset}
          className="inline-flex h-11 items-center justify-center gap-2 rounded-xl border border-white/10 bg-white/[0.04] px-4 text-sm font-semibold text-stone-300 transition hover:border-gold/30 hover:text-gold"
        >
          <RotateCcw size={16} />
          Reset
        </button>
      </div>

      <p className="mt-4 text-xs leading-5 text-stone-500">
        Equal ratings are rejected by the backend because upset prediction requires a rating gap.
      </p>
    </section>
  );
}

function NumberField({
  label,
  value,
  min,
  onChange,
}: {
  label: string;
  value: number;
  min: number;
  onChange: (value: number) => void;
}) {
  return (
    <label className="block">
      <span className="mb-1.5 block font-mono text-[0.62rem] uppercase tracking-[0.18em] text-stone-500">
        {label}
      </span>
      <input
        type="number"
        min={min}
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
        className="h-11 w-full rounded-xl border border-white/10 bg-black/35 px-3 text-sm text-ivory outline-none transition focus:border-gold/60 focus:ring-2 focus:ring-gold/15"
      />
    </label>
  );
}
