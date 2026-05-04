"""Build mid-game snapshot parquet datasets from filtered games."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Sequence

import pandas as pd

from plyshock.features.snapshot_builder import (
    DEFAULT_SNAPSHOT_MOVES,
    SNAPSHOT_COLUMNS,
    build_snapshots_from_game_record,
)


def build_snapshots_dataset(
    input_path: str | Path,
    output_path: str | Path,
    summary_path: str | Path,
    snapshot_moves: list[int] | None = None,
) -> dict[str, object]:
    """Build a snapshot parquet dataset and JSON summary from filtered games.

    Args:
        input_path: Source filtered games parquet path.
        output_path: Destination snapshot parquet path.
        summary_path: Destination summary JSON path.
        snapshot_moves: Fullmove numbers to snapshot. Defaults to ``[15, 20, 25, 30, 35]``.

    Returns:
        Summary dictionary written to ``summary_path``.
    """
    parquet_path = Path(input_path)
    snapshots_path = Path(output_path)
    report_path = Path(summary_path)
    selected_moves = snapshot_moves or DEFAULT_SNAPSHOT_MOVES

    games_dataframe = pd.read_parquet(parquet_path)
    snapshot_records: list[dict[str, object]] = []
    snapshot_counts: Counter[str] = Counter({str(move): 0 for move in selected_moves})
    games_with_zero_snapshots = 0

    for record in games_dataframe.to_dict(orient="records"):
        game_snapshots = build_snapshots_from_game_record(record, selected_moves)
        if not game_snapshots:
            games_with_zero_snapshots += 1
            continue

        snapshot_records.extend(game_snapshots)
        snapshot_counts.update(str(snapshot["snapshot_move"]) for snapshot in game_snapshots)

    _write_snapshots(snapshot_records, snapshots_path)

    upset_snapshot_count = sum(
        1 for snapshot in snapshot_records if int(snapshot["upset_label"]) == 1
    )
    non_upset_snapshot_count = sum(
        1 for snapshot in snapshot_records if int(snapshot["upset_label"]) == 0
    )
    summary: dict[str, object] = {
        "input_path": str(parquet_path),
        "output_path": str(snapshots_path),
        "total_games": int(len(games_dataframe)),
        "total_snapshots": len(snapshot_records),
        "snapshot_moves": selected_moves,
        "snapshot_counts_by_move": dict(sorted(snapshot_counts.items())),
        "games_with_zero_snapshots": games_with_zero_snapshots,
        "upset_snapshot_count": upset_snapshot_count,
        "non_upset_snapshot_count": non_upset_snapshot_count,
    }
    _write_summary(summary, report_path)
    return summary


def main(argv: Sequence[str] | None = None) -> None:
    """Run the snapshot-building pipeline from the command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Input filtered parquet path.")
    parser.add_argument("--output", required=True, type=Path, help="Output snapshots parquet path.")
    parser.add_argument("--summary", required=True, type=Path, help="Output summary JSON path.")
    parser.add_argument(
        "--snapshot-moves",
        nargs="*",
        type=int,
        default=None,
        help="Fullmove numbers to snapshot. Defaults to 15 20 25 30 35.",
    )
    args = parser.parse_args(argv)

    build_snapshots_dataset(
        input_path=args.input,
        output_path=args.output,
        summary_path=args.summary,
        snapshot_moves=args.snapshot_moves,
    )


def _write_snapshots(records: list[dict[str, object]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    dataframe = pd.DataFrame.from_records(records, columns=SNAPSHOT_COLUMNS)
    dataframe.to_parquet(output_path, index=False)


def _write_summary(summary: dict[str, object], summary_path: Path) -> None:
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
