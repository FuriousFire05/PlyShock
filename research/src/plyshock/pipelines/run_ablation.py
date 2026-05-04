"""Run PlyShock ablation studies from a feature dataset."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

import pandas as pd

from plyshock.evaluation.ablation import run_ablation_study


def main(argv: Sequence[str] | None = None) -> None:
    """Run the ablation pipeline from the command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--features", required=True, type=Path, help="Input feature parquet path.")
    parser.add_argument(
        "--schema", required=True, type=Path, help="Input feature schema JSON path."
    )
    parser.add_argument("--output-json", required=True, type=Path, help="Output metrics JSON path.")
    parser.add_argument("--output-plot", required=True, type=Path, help="Output F1 plot path.")
    parser.add_argument("--test-size", default=0.2, type=float, help="Test split fraction.")
    parser.add_argument("--random-state", default=42, type=int, help="Random seed.")
    args = parser.parse_args(argv)

    dataframe = pd.read_parquet(args.features)
    feature_schema = json.loads(args.schema.read_text(encoding="utf-8"))
    run_ablation_study(
        dataframe,
        feature_schema,
        output_metrics_path=args.output_json,
        output_plot_path=args.output_plot,
        test_size=args.test_size,
        random_state=args.random_state,
    )


if __name__ == "__main__":
    main()
