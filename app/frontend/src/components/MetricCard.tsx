import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

type Tone = "gold" | "green" | "red" | "ivory" | "muted";

const toneClasses: Record<Tone, string> = {
  gold: "border-gold/30 bg-gold/[0.075] text-gold",
  green: "border-green-400/25 bg-green-400/[0.06] text-green-300",
  red: "border-red-400/25 bg-red-400/[0.06] text-red-300",
  ivory: "border-ivory/15 bg-ivory/[0.045] text-ivory",
  muted: "border-white/10 bg-white/[0.035] text-stone-300",
};

interface MetricCardProps {
  label: string;
  value: string | number;
  detail?: string;
  icon?: LucideIcon;
  tone?: Tone;
}

export function MetricCard({ label, value, detail, icon: Icon, tone = "muted" }: MetricCardProps) {
  return (
    <div className={cn("panel min-h-28 border p-4", toneClasses[tone])}>
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="font-mono text-[0.66rem] uppercase tracking-[0.2em] text-stone-400">
            {label}
          </p>
          <p className="mt-3 text-2xl font-semibold tracking-tight text-ivory">{value}</p>
        </div>
        {Icon ? (
          <div className="rounded-lg border border-current/20 bg-black/25 p-2">
            <Icon size={18} />
          </div>
        ) : null}
      </div>
      {detail ? <p className="mt-3 text-sm leading-6 text-stone-400">{detail}</p> : null}
    </div>
  );
}
