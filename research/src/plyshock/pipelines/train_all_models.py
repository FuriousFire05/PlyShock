"""Train all PlyShock classical models from a feature dataset."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

import pandas as pd

from plyshock.training.train_models import train_and_evaluate_models


def main(argv: Sequence[str] | None = None) -> None:
    """Run the model training pipeline from the command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--features", required=True, type=Path, help="Input feature parquet path.")
    parser.add_argument(
        "--schema", required=True, type=Path, help="Input feature schema JSON path."
    )
    parser.add_argument("--models-dir", required=True, type=Path, help="Output model directory.")
    parser.add_argument("--metrics-dir", required=True, type=Path, help="Output metrics directory.")
    parser.add_argument("--plots-dir", required=True, type=Path, help="Output plots directory.")
    parser.add_argument("--test-size", default=0.2, type=float, help="Test split fraction.")
    parser.add_argument("--random-state", default=42, type=int, help="Random seed.")
    args = parser.parse_args(argv)

    feature_df = pd.read_parquet(args.features)
    feature_schema = json.loads(args.schema.read_text(encoding="utf-8"))
    train_and_evaluate_models(
        feature_df,
        feature_schema,
        output_dir=args.models_dir,
        metrics_dir=args.metrics_dir,
        plots_dir=args.plots_dir,
        test_size=args.test_size,
        random_state=args.random_state,
    )


if __name__ == "__main__":
    main()
