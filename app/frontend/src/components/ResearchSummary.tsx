import { BarChart3, Brain, GitBranch, Layers3, Scale, Spline } from "lucide-react";
import { formatMetric } from "@/lib/utils";
import { MetricCard } from "./MetricCard";

export function ResearchSummary() {
  return (
    <section className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="font-mono text-[0.66rem] uppercase tracking-[0.22em] text-gold">
            Research backbone
          </p>
          <h2 className="mt-2 text-2xl font-semibold text-ivory">
            Dynamic Upset Prediction in Chess
          </h2>
        </div>
        <p className="max-w-2xl text-sm leading-6 text-stone-400">
          PlyShock is trained on sampled Lichess PGN .zst data. The grouped game-level split by
          game_id avoids snapshot leakage between train and test positions.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <MetricCard label="Filtered games" value="6,537" detail="Project-qualified decisive games." icon={Layers3} tone="ivory" />
        <MetricCard label="Snapshot rows" value="24,563" detail="Mid-game checkpoint positions." icon={Spline} tone="gold" />
        <MetricCard label="Features" value="26" detail="Rating, clock, engine, and trends." icon={Brain} tone="green" />
        <MetricCard label="Models" value="5" detail="Decision Tree, KNN, Naive Bayes, SVM, Random Forest." icon={BarChart3} tone="muted" />
        <MetricCard label="Split" value="Grouped" detail="Game-level split by game_id." icon={GitBranch} tone="ivory" />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <MetricCard
          label="Random Forest"
          value={`${formatMetric(0.762)} accuracy`}
          detail={`Best accuracy with ROC-AUC ${formatMetric(0.813)}.`}
          icon={BarChart3}
          tone="gold"
        />
        <MetricCard
          label="SVM"
          value={`${formatMetric(0.733)} recall`}
          detail={`Best recall with F1 ${formatMetric(0.634)}.`}
          icon={Brain}
          tone="green"
        />
        <MetricCard
          label="Ablation"
          value={`${formatMetric(0.811)} ROC-AUC`}
          detail={`Rating + clock + engine beats rating-only ROC-AUC ${formatMetric(0.586)}; full PlyShock reaches ${formatMetric(0.813)}.`}
          icon={Scale}
          tone="ivory"
        />
      </div>

      <div className="panel border border-gold/15 bg-gold/[0.05] p-5">
        <p className="font-mono text-[0.66rem] uppercase tracking-[0.22em] text-gold">
          Scientific honesty
        </p>
        <div className="mt-3 grid gap-3 text-sm leading-6 text-stone-300 md:grid-cols-3">
          <p>Stockfish eval updates every move in the replay endpoint.</p>
          <p>PlyShock predictions update only at trained checkpoints: moves 15, 20, 25, 30, 35.</p>
          <p>Outputs are upset probability estimates, not perfect chess outcome claims.</p>
        </div>
      </div>
    </section>
  );
}
