"""Run minimal EDA for the filtered PlyShock games dataset."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

import matplotlib.pyplot as plt
import pandas as pd

REQUIRED_COLUMNS = {"game_id", "rating_gap", "upset_label", "final_fullmove_number"}
RATING_GAP_BINS = [0, 100, 200, 400, 800, float("inf")]
RATING_GAP_LABELS = ["0-99", "100-199", "200-399", "400-799", "800+"]
PLOT_FILENAMES = [
    "upset_class_distribution.png",
    "rating_gap_distribution.png",
    "upset_rate_by_rating_gap_bucket.png",
    "game_length_distribution.png",
]


def run_eda(
    input_path: str | Path, metrics_output_path: str | Path, plots_dir: str | Path
) -> dict[str, object]:
    """Generate EDA metrics and plots for a filtered games parquet dataset.

    Args:
        input_path: Path to the filtered games parquet file.
        metrics_output_path: Destination path for metrics JSON.
        plots_dir: Directory where plot PNG files will be written.

    Returns:
        Metrics dictionary written to ``metrics_output_path``.

    Raises:
        ValueError: If the dataset is empty or missing required columns.
    """
    parquet_path = Path(input_path)
    metrics_path = Path(metrics_output_path)
    plot_directory = Path(plots_dir)

    dataframe = pd.read_parquet(parquet_path)
    _validate_dataframe(dataframe)

    metrics = _build_metrics(dataframe)

    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    plot_directory.mkdir(parents=True, exist_ok=True)
    _write_plots(dataframe, plot_directory)

    return metrics


def main(argv: Sequence[str] | None = None) -> None:
    """Run the EDA pipeline from the command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Input filtered parquet path.")
    parser.add_argument(
        "--metrics-output", required=True, type=Path, help="Output metrics JSON path."
    )
    parser.add_argument("--plots-dir", required=True, type=Path, help="Output plots directory.")
    args = parser.parse_args(argv)

    run_eda(
        input_path=args.input,
        metrics_output_path=args.metrics_output,
        plots_dir=args.plots_dir,
    )


def _validate_dataframe(dataframe: pd.DataFrame) -> None:
    missing_columns = REQUIRED_COLUMNS.difference(dataframe.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Filtered games dataset is missing required columns: {missing}.")

    if dataframe.empty:
        raise ValueError("Filtered games dataset is empty; EDA requires at least one game.")


def _build_metrics(dataframe: pd.DataFrame) -> dict[str, object]:
    total_games = int(len(dataframe))
    upset_count = int((dataframe["upset_label"] == 1).sum())
    non_upset_count = int((dataframe["upset_label"] == 0).sum())
    rating_gap_buckets = _rating_gap_buckets(dataframe)
    bucket_counts = rating_gap_buckets.value_counts(sort=False)
    upset_rates_by_bucket = dataframe.groupby(rating_gap_buckets, observed=True)[
        "upset_label"
    ].mean()

    return {
        "total_games": total_games,
        "upset_count": upset_count,
        "non_upset_count": non_upset_count,
        "upset_rate": float(upset_count / total_games),
        "rating_gap_min": int(dataframe["rating_gap"].min()),
        "rating_gap_max": int(dataframe["rating_gap"].max()),
        "rating_gap_mean": float(dataframe["rating_gap"].mean()),
        "final_fullmove_min": int(dataframe["final_fullmove_number"].min()),
        "final_fullmove_max": int(dataframe["final_fullmove_number"].max()),
        "final_fullmove_mean": float(dataframe["final_fullmove_number"].mean()),
        "rating_gap_bucket_counts": _series_to_int_dict(bucket_counts),
        "upset_rate_by_rating_gap_bucket": _series_to_float_dict(upset_rates_by_bucket),
    }


def _write_plots(dataframe: pd.DataFrame, plots_dir: Path) -> None:
    _plot_upset_class_distribution(dataframe, plots_dir / PLOT_FILENAMES[0])
    _plot_rating_gap_distribution(dataframe, plots_dir / PLOT_FILENAMES[1])
    _plot_upset_rate_by_rating_gap_bucket(dataframe, plots_dir / PLOT_FILENAMES[2])
    _plot_game_length_distribution(dataframe, plots_dir / PLOT_FILENAMES[3])


def _plot_upset_class_distribution(dataframe: pd.DataFrame, output_path: Path) -> None:
    counts = dataframe["upset_label"].value_counts().reindex([0, 1], fill_value=0)
    figure, axis = plt.subplots()
    axis.bar(["non_upset", "upset"], counts.to_list())
    axis.set_title("Upset Class Distribution")
    axis.set_xlabel("Class")
    axis.set_ylabel("Games")
    figure.tight_layout()
    figure.savefig(output_path)
    plt.close(figure)


def _plot_rating_gap_distribution(dataframe: pd.DataFrame, output_path: Path) -> None:
    figure, axis = plt.subplots()
    axis.hist(dataframe["rating_gap"])
    axis.set_title("Rating Gap Distribution")
    axis.set_xlabel("Rating gap")
    axis.set_ylabel("Games")
    figure.tight_layout()
    figure.savefig(output_path)
    plt.close(figure)


def _plot_upset_rate_by_rating_gap_bucket(dataframe: pd.DataFrame, output_path: Path) -> None:
    buckets = _rating_gap_buckets(dataframe)
    upset_rates = dataframe.groupby(buckets, observed=True)["upset_label"].mean()
    figure, axis = plt.subplots()
    axis.bar([str(index) for index in upset_rates.index], upset_rates.to_list())
    axis.set_title("Upset Rate by Rating Gap Bucket")
    axis.set_xlabel("Rating gap bucket")
    axis.set_ylabel("Upset rate")
    figure.autofmt_xdate(rotation=45)
    figure.tight_layout()
    figure.savefig(output_path)
    plt.close(figure)


def _plot_game_length_distribution(dataframe: pd.DataFrame, output_path: Path) -> None:
    figure, axis = plt.subplots()
    axis.hist(dataframe["final_fullmove_number"])
    axis.set_title("Game Length Distribution")
    axis.set_xlabel("Final fullmove number")
    axis.set_ylabel("Games")
    figure.tight_layout()
    figure.savefig(output_path)
    plt.close(figure)


def _rating_gap_buckets(dataframe: pd.DataFrame) -> pd.Series:
    return pd.cut(
        dataframe["rating_gap"],
        bins=RATING_GAP_BINS,
        labels=RATING_GAP_LABELS,
        right=False,
        include_lowest=True,
    )


def _series_to_int_dict(series: pd.Series) -> dict[str, int]:
    return {str(index): int(value) for index, value in series.items()}


def _series_to_float_dict(series: pd.Series) -> dict[str, float]:
    return {str(index): float(value) for index, value in series.items()}


if __name__ == "__main__":
    main()
