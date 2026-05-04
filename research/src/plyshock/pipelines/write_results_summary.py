"""Write a report-ready Markdown summary from PlyShock metrics JSON files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

METRIC_COLUMNS = ["accuracy", "precision", "recall", "f1", "roc_auc"]


def write_results_summary(
    model_comparison_path: str | Path,
    eda_summary_path: str | Path,
    output_path: str | Path,
) -> str:
    """Create and write a Markdown results summary.

    Args:
        model_comparison_path: Path to ``model_comparison.json``.
        eda_summary_path: Path to EDA summary JSON.
        output_path: Destination Markdown path.

    Returns:
        The Markdown content written to ``output_path``.
    """
    model_summary = _read_json(model_comparison_path)
    eda_summary = _read_json(eda_summary_path)
    content = _build_markdown_summary(model_summary, eda_summary)

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")
    return content


def main(argv: Sequence[str] | None = None) -> None:
    """Run the results summary writer from the command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models-json", required=True, type=Path, help="Model comparison JSON.")
    parser.add_argument("--eda-json", required=True, type=Path, help="EDA summary JSON.")
    parser.add_argument("--output", required=True, type=Path, help="Output Markdown path.")
    args = parser.parse_args(argv)

    write_results_summary(
        model_comparison_path=args.models_json,
        eda_summary_path=args.eda_json,
        output_path=args.output,
    )


def _build_markdown_summary(
    model_summary: dict[str, object], eda_summary: dict[str, object]
) -> str:
    models = _models_dict(model_summary)
    best_by_f1 = _best_model_by_metric(models, "f1")
    best_by_roc_auc = _best_model_by_metric(models, "roc_auc")
    best_by_accuracy = _best_model_by_metric(models, "accuracy")
    model_table = _model_comparison_table(models)
    bucket_rates = _rating_gap_bucket_rates(eda_summary)

    return "\n".join(
        [
            "# PlyShock Results Summary",
            "",
            "## Dataset Summary",
            f"- Total model rows: {model_summary.get('total_rows', 'n/a')}",
            f"- Train rows: {model_summary.get('train_rows', 'n/a')}",
            f"- Test rows: {model_summary.get('test_rows', 'n/a')}",
            f"- Train games: {model_summary.get('train_games', 'n/a')}",
            f"- Test games: {model_summary.get('test_games', 'n/a')}",
            f"- Feature count: {model_summary.get('feature_count', 'n/a')}",
            f"- Upset count: {eda_summary.get('upset_count', 'n/a')}",
            f"- Non-upset count: {eda_summary.get('non_upset_count', 'n/a')}",
            f"- Upset rate: {_format_metric(eda_summary.get('upset_rate'))}",
            "",
            "## Preprocessing and EDA Highlights",
            f"- Rating gap min: {eda_summary.get('rating_gap_min', 'n/a')}",
            f"- Rating gap max: {eda_summary.get('rating_gap_max', 'n/a')}",
            f"- Rating gap mean: {_format_metric(eda_summary.get('rating_gap_mean'))}",
            "- Rating gap bucket upset rates:",
            bucket_rates,
            "",
            "## Model Training Setup",
            "- Models were trained on schema-declared model input features only.",
            "- Metadata and leakage-prone fields such as game_id, FEN, result, winner color, "
            "final fullmove number, and time control string were not used as model inputs.",
            "- The train/test split is grouped by game so snapshots from the same game do not "
            "appear in both splits.",
            f"- Target column: {model_summary.get('target_column', 'n/a')}",
            "",
            "## Model Comparison Table",
            model_table,
            "",
            "## Best Model Discussion",
            f"- Best model by F1: {best_by_f1}.",
            f"- Best model by ROC-AUC: {best_by_roc_auc}.",
            f"- Best model by accuracy: {best_by_accuracy}.",
            "- These results indicate which classical model performed better under each metric "
            "within this dataset; they do not prove a general relationship outside the "
            "sampled data.",
            "",
            "## Final Report Interpretation Points",
            "- Class balance and rating-gap bucket behavior should be interpreted alongside model "
            "metrics because upset prediction is sensitive to dataset composition.",
            "- Metric differences suggest comparative performance within this dataset, but further "
            "validation on held-out months or larger samples would strengthen the conclusion.",
            "- Engine-derived and clock-derived features may capture useful mid-game context, "
            "but the summary should avoid causal claims without additional experimental controls.",
            "",
        ]
    )


def _model_comparison_table(models: dict[str, dict[str, object]]) -> str:
    rows = [
        "| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for model_name, metrics in models.items():
        rows.append(
            "| "
            + " | ".join(
                [
                    model_name,
                    *[_format_metric(metrics.get(metric)) for metric in METRIC_COLUMNS],
                ]
            )
            + " |"
        )
    return "\n".join(rows)


def _rating_gap_bucket_rates(eda_summary: dict[str, object]) -> str:
    rates = eda_summary.get("upset_rate_by_rating_gap_bucket", {})
    if not isinstance(rates, dict) or not rates:
        return "  - n/a"
    return "\n".join(
        f"  - {bucket}: {_format_metric(rate)}" for bucket, rate in sorted(rates.items())
    )


def _best_model_by_metric(models: dict[str, dict[str, object]], metric: str) -> str:
    best_model = None
    best_value = None
    for model_name, metrics in models.items():
        value = metrics.get(metric)
        if value is None:
            continue
        numeric_value = float(value)
        if best_value is None or numeric_value > best_value:
            best_model = model_name
            best_value = numeric_value

    if best_model is None:
        return "n/a"
    return f"{best_model} ({_format_metric(best_value)})"


def _format_metric(value: object) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, int | float):
        return f"{float(value):.3f}"
    return str(value)


def _models_dict(model_summary: dict[str, object]) -> dict[str, dict[str, object]]:
    models = model_summary.get("models", {})
    if not isinstance(models, dict):
        return {}
    return {
        str(model_name): dict(metrics)
        for model_name, metrics in models.items()
        if isinstance(metrics, dict)
    }


def _read_json(path: str | Path) -> dict[str, object]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
