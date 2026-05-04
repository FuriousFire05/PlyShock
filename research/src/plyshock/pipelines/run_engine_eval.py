"""Evaluate snapshot FENs with Stockfish and maintain a parquet cache."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Sequence

import pandas as pd

from plyshock.engine.eval_cache import (
    EVAL_COLUMNS,
    fen_hash,
    load_eval_cache,
    merge_missing_evals,
    save_eval_cache,
)
from plyshock.engine.stockfish_client import evaluate_fens


def run_engine_eval(
    snapshots_path: str | Path,
    cache_path: str | Path,
    output_path: str | Path,
    engine_path: str | Path,
    depth: int = 8,
    max_fens: int | None = None,
    summary_path: str | Path | None = None,
) -> dict[str, object]:
    """Evaluate missing snapshot FENs, update cache, and write enriched snapshots.

    Args:
        snapshots_path: Input snapshots parquet path.
        cache_path: Evaluation cache parquet path.
        output_path: Output snapshots parquet path with evaluation columns.
        engine_path: Stockfish executable path.
        depth: Stockfish analysis depth.
        max_fens: Optional limit on newly evaluated unique FENs.
        summary_path: Optional summary JSON path. Defaults next to ``output_path``.

    Returns:
        Summary dictionary written to JSON.
    """
    snapshot_file = Path(snapshots_path)
    cache_file = Path(cache_path)
    output_file = Path(output_path)
    engine_file = Path(engine_path)
    report_file = (
        Path(summary_path) if summary_path is not None else output_file.with_suffix(".summary.json")
    )

    snapshots = pd.read_parquet(snapshot_file)
    cache = load_eval_cache(cache_file)
    _, missing_fens = merge_missing_evals(snapshots, cache)
    fens_to_evaluate = missing_fens[:max_fens] if max_fens is not None else missing_fens

    print(f"Loaded {len(snapshots)} snapshots.")
    print(f"Cache has {len(cache)} evaluations; {len(missing_fens)} unique FENs are missing.")
    print(f"Evaluating {len(fens_to_evaluate)} FENs at depth {depth}.")

    new_records: list[dict[str, object]] = []
    evaluations = (
        evaluate_fens(engine_file, fens_to_evaluate, depth=depth) if fens_to_evaluate else []
    )
    for index, evaluation in enumerate(evaluations, start=1):
        record = asdict(evaluation)
        record["fen_hash"] = fen_hash(evaluation.fen)
        new_records.append(record)
        if index % 100 == 0 or index == len(evaluations):
            print(f"Prepared {index}/{len(evaluations)} new cache records.")

    updated_cache = _updated_cache(cache, new_records)
    save_eval_cache(updated_cache, cache_file)

    enriched_snapshots, still_missing_fens = merge_missing_evals(snapshots, updated_cache)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    enriched_snapshots.to_parquet(output_file, index=False)

    summary: dict[str, object] = {
        "snapshots_path": str(snapshot_file),
        "cache_path": str(cache_file),
        "output_path": str(output_file),
        "engine_path": str(engine_file),
        "depth": depth,
        "max_fens": max_fens,
        "snapshot_rows": int(len(snapshots)),
        "cache_rows": int(len(updated_cache)),
        "missing_fens_before": len(missing_fens),
        "evaluated_fens": len(new_records),
        "missing_fens_after": len(still_missing_fens),
    }
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Wrote enriched snapshots to {output_file}.")
    print(f"Wrote summary to {report_file}.")
    return summary


def main(argv: Sequence[str] | None = None) -> None:
    """Run the engine evaluation pipeline from the command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--snapshots", required=True, type=Path, help="Input snapshots parquet path."
    )
    parser.add_argument("--cache", required=True, type=Path, help="Evaluation cache parquet path.")
    parser.add_argument("--output", required=True, type=Path, help="Output enriched parquet path.")
    parser.add_argument(
        "--engine-path", required=True, type=Path, help="Stockfish executable path."
    )
    parser.add_argument("--depth", default=8, type=int, help="Stockfish search depth.")
    parser.add_argument("--max-fens", default=None, type=int, help="Maximum new FENs to evaluate.")
    parser.add_argument(
        "--summary", default=None, type=Path, help="Optional output summary JSON path."
    )
    args = parser.parse_args(argv)

    run_engine_eval(
        snapshots_path=args.snapshots,
        cache_path=args.cache,
        output_path=args.output,
        engine_path=args.engine_path,
        depth=args.depth,
        max_fens=args.max_fens,
        summary_path=args.summary,
    )


def _updated_cache(cache: pd.DataFrame, new_records: list[dict[str, object]]) -> pd.DataFrame:
    if new_records:
        new_cache = pd.DataFrame.from_records(new_records, columns=EVAL_COLUMNS)
        updated = pd.concat([cache.reindex(columns=EVAL_COLUMNS), new_cache], ignore_index=True)
    else:
        updated = cache.reindex(columns=EVAL_COLUMNS)
    return updated.drop_duplicates("fen_hash", keep="last")


if __name__ == "__main__":
    main()
