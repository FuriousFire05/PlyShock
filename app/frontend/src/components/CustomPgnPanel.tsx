import { ClipboardPaste, FileSearch } from "lucide-react";

interface CustomPgnPanelProps {
  value: string;
  loading: boolean;
  error: string | null;
  hasReplay: boolean;
  onChange: (value: string) => void;
  onAnalyze: () => void;
}

export function CustomPgnPanel({
  value,
  loading,
  error,
  hasReplay,
  onChange,
  onAnalyze,
}: CustomPgnPanelProps) {
  return (
    <section className="panel border border-white/10 p-5">
      <div className="mb-4 flex items-center justify-between gap-4">
        <div>
          <p className="font-mono text-[0.66rem] uppercase tracking-[0.22em] text-gold">
            Paste PGN
          </p>
          <h2 className="mt-2 text-xl font-semibold text-ivory">Custom replay analysis</h2>
        </div>
        <ClipboardPaste className="text-gold" size={22} />
      </div>

      <textarea
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder='[Event "Rated Blitz game"]&#10;[WhiteElo "1500"]&#10;[BlackElo "1700"]&#10;...'
        className="min-h-72 w-full resize-y rounded-2xl border border-white/10 bg-black/35 p-4 font-mono text-xs leading-6 text-ivory outline-none transition placeholder:text-stone-600 focus:border-gold/60 focus:ring-2 focus:ring-gold/15"
      />

      {error ? (
        <div className="mt-4 rounded-2xl border border-red-400/25 bg-red-400/[0.06] p-4 text-sm leading-6 text-red-100">
          {error}
        </div>
      ) : null}

      <button
        type="button"
        onClick={onAnalyze}
        disabled={loading || value.trim().length === 0}
        className="mt-4 inline-flex h-12 w-full items-center justify-center gap-2 rounded-xl border border-gold/35 bg-gold/16 px-4 text-sm font-semibold text-ivory transition hover:bg-gold/22 disabled:cursor-not-allowed disabled:opacity-45"
      >
        <FileSearch size={17} />
        {loading ? "Analyzing PGN..." : hasReplay ? "Analyze again" : "Analyze PGN"}
      </button>

      <p className="mt-4 text-xs leading-5 text-stone-500">
        PGN must include Elo headers and clock comments for full PlyShock analysis. The backend
        validates the same project rules used by the trained demo pipeline.
      </p>
    </section>
  );
}
