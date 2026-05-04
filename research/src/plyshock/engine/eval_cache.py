"""Parquet-backed evaluation cache helpers for snapshot FENs."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

EVAL_COLUMNS = [
    "fen_hash",
    "fen",
    "eval_cp_white_pov",
    "eval_cp_clipped",
    "mate_flag",
    "depth",
]


def fen_hash(fen: str) -> str:
    """Return a stable SHA-256 hash for a FEN string."""
    return hashlib.sha256(fen.encode("utf-8")).hexdigest()


def load_eval_cache(path: str | Path) -> pd.DataFrame:
    """Load an evaluation cache parquet file or return an empty cache frame."""
    cache_path = Path(path)
    if cache_path.exists():
        return pd.read_parquet(cache_path)
    return pd.DataFrame(columns=EVAL_COLUMNS)


def save_eval_cache(df: pd.DataFrame, path: str | Path) -> None:
    """Save an evaluation cache dataframe to parquet."""
    cache_path = Path(path)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    dataframe = df.reindex(columns=EVAL_COLUMNS)
    dataframe.to_parquet(cache_path, index=False)


def merge_missing_evals(
    snapshot_df: pd.DataFrame, cache_df: pd.DataFrame
) -> tuple[pd.DataFrame, list[str]]:
    """Merge cached evaluations onto snapshots and list unique FENs still missing.

    Args:
        snapshot_df: Snapshot rows containing a ``fen`` column.
        cache_df: Existing evaluation cache.

    Returns:
        A tuple of ``(merged_dataframe, missing_fens)``.
    """
    if "fen" not in snapshot_df.columns:
        raise ValueError("Snapshot dataframe must contain a 'fen' column.")

    snapshots = snapshot_df.copy()
    snapshots["fen_hash"] = snapshots["fen"].map(fen_hash)
    cache = cache_df.reindex(columns=EVAL_COLUMNS).drop_duplicates("fen_hash", keep="last")
    merged = snapshots.merge(
        cache.drop(columns=["fen"], errors="ignore"),
        on="fen_hash",
        how="left",
    )

    cached_hashes = set(cache["fen_hash"].dropna())
    missing_fens: list[str] = []
    seen_hashes: set[str] = set()
    for fen, hashed_fen in zip(snapshots["fen"], snapshots["fen_hash"], strict=True):
        if hashed_fen in cached_hashes or hashed_fen in seen_hashes:
            continue
        missing_fens.append(str(fen))
        seen_hashes.add(str(hashed_fen))

    return merged, missing_fens
