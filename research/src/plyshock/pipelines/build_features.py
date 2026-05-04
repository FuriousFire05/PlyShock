"""Build the final ML-ready feature dataset from evaluated snapshots."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

import pandas as pd

from plyshock.features.feature_pipeline import (
    METADATA_COLUMNS,
    MODEL_INPUT_FEATURES,
    TARGET_COLUMN,
    build_feature_dataframe,
    write_feature_schema,
)


def build_features_dataset(
    input_path: str | Path,
    output_path: str | Path,
    schema_path: str | Path,
    summary_path: str | Path,
) -> dict[str, object]:
    """Build and save the final feature dataset, schema JSON, and summary JSON.

    Args:
        input_path: Source evaluated snapshots parquet path.
        output_path: Destination feature parquet path.
        schema_path: Destination feature schema JSON path.
        summary_path: Destination summary JSON path.

    Returns:
        Summary dictionary written to ``summary_path``.
    """
    source_path = Path(input_path)
    feature_path = Path(output_path)
    schema_file = Path(schema_path)
    report_path = Path(summary_path)

    snapshots = pd.read_parquet(source_path)
    total_input_rows = int(len(snapshots))
    evaluated_snapshots = snapshots.dropna(subset=["eval_cp_white_pov"]).copy()
    dropped_missing_eval_rows = total_input_rows - int(len(evaluated_snapshots))
    features = build_feature_dataframe(evaluated_snapshots)

    feature_path.parent.mkdir(parents=True, exist_ok=True)
    features.to_parquet(feature_path, index=False)
    write_feature_schema(
        schema_file,
        model_input_features=MODEL_INPUT_FEATURES,
        metadata_columns=METADATA_COLUMNS,
        target_column=TARGET_COLUMN,
    )

    summary: dict[str, object] = {
        "input_path": str(source_path),
        "output_path": str(feature_path),
        "total_input_rows": total_input_rows,
        "total_output_rows": int(len(features)),
        "dropped_missing_eval_rows": dropped_missing_eval_rows,
        "feature_count": len(MODEL_INPUT_FEATURES),
        "upset_count": int((features[TARGET_COLUMN] == 1).sum()),
        "non_upset_count": int((features[TARGET_COLUMN] == 0).sum()),
        "snapshot_counts_by_move": _snapshot_counts_by_move(features),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main(argv: Sequence[str] | None = None) -> None:
    """Run the feature-building pipeline from the command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input", required=True, type=Path, help="Input evaluated snapshots parquet."
    )
    parser.add_argument("--output", required=True, type=Path, help="Output feature parquet path.")
    parser.add_argument(
        "--schema", required=True, type=Path, help="Output feature schema JSON path."
    )
    parser.add_argument("--summary", required=True, type=Path, help="Output summary JSON path.")
    args = parser.parse_args(argv)

    build_features_dataset(
        input_path=args.input,
        output_path=args.output,
        schema_path=args.schema,
        summary_path=args.summary,
    )


def _snapshot_counts_by_move(dataframe: pd.DataFrame) -> dict[str, int]:
    if dataframe.empty:
        return {}
    counts = dataframe["snapshot_move"].value_counts().sort_index()
    return {str(int(snapshot_move)): int(count) for snapshot_move, count in counts.items()}


if __name__ == "__main__":
    main()
