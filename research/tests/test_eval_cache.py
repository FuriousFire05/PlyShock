from pathlib import Path

import pandas as pd
from plyshock.engine.eval_cache import EVAL_COLUMNS, fen_hash, load_eval_cache, merge_missing_evals


def test_fen_hash_is_stable() -> None:
    fen = "8/8/8/8/8/8/8/8 w - - 0 1"

    assert fen_hash(fen) == fen_hash(fen)
    assert len(fen_hash(fen)) == 64


def test_fen_hash_differs_for_different_fens() -> None:
    assert fen_hash("8/8/8/8/8/8/8/8 w - - 0 1") != fen_hash(
        "8/8/8/8/8/8/8/8 b - - 0 1"
    )


def test_load_eval_cache_missing_path_returns_empty_frame(tmp_path: Path) -> None:
    cache = load_eval_cache(tmp_path / "missing.parquet")

    assert cache.empty
    assert list(cache.columns) == EVAL_COLUMNS


def test_merge_missing_evals_merges_cached_rows_and_lists_unique_missing_fens() -> None:
    cached_fen = "8/8/8/8/8/8/8/8 w - - 0 1"
    missing_fen = "8/8/8/8/8/8/8/8 b - - 0 1"
    snapshot_df = pd.DataFrame(
        {
            "snapshot_id": [1, 2, 3],
            "fen": [cached_fen, missing_fen, missing_fen],
        }
    )
    cache_df = pd.DataFrame(
        [
            {
                "fen_hash": fen_hash(cached_fen),
                "fen": cached_fen,
                "eval_cp_white_pov": 42,
                "eval_cp_clipped": 42,
                "mate_flag": False,
                "depth": 8,
            }
        ]
    )

    merged, missing_fens = merge_missing_evals(snapshot_df, cache_df)

    assert missing_fens == [missing_fen]
    assert merged.loc[0, "fen_hash"] == fen_hash(cached_fen)
    assert merged.loc[0, "eval_cp_white_pov"] == 42
    assert pd.isna(merged.loc[1, "eval_cp_white_pov"])
    assert pd.isna(merged.loc[2, "eval_cp_white_pov"])


def test_merge_missing_evals_with_empty_cache_marks_all_unique_fens_missing() -> None:
    first_fen = "8/8/8/8/8/8/8/8 w - - 0 1"
    second_fen = "8/8/8/8/8/8/8/8 b - - 0 1"
    snapshot_df = pd.DataFrame({"fen": [first_fen, second_fen, first_fen]})

    merged, missing_fens = merge_missing_evals(snapshot_df, pd.DataFrame(columns=EVAL_COLUMNS))

    assert missing_fens == [first_fen, second_fen]
    assert "fen_hash" in merged.columns
    assert merged["eval_cp_white_pov"].isna().all()
