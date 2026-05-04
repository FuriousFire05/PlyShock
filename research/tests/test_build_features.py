import json
from pathlib import Path

import pandas as pd
from plyshock.pipelines.build_features import build_features_dataset


def test_build_features_dataset_writes_parquet_schema_and_summary(tmp_path: Path) -> None:
    input_path = tmp_path / "snapshots_with_eval.parquet"
    output_path = tmp_path / "features.parquet"
    schema_path = tmp_path / "feature_schema.json"
    summary_path = tmp_path / "feature_summary.json"
    pd.DataFrame(
        [
            _snapshot_row("game-1", 15, eval_cp_white_pov=100),
            _snapshot_row("game-1", 20, eval_cp_white_pov=250),
            _snapshot_row("game-2", 15, eval_cp_white_pov=None),
        ]
    ).to_parquet(input_path, index=False)

    summary = build_features_dataset(input_path, output_path, schema_path, summary_path)

    assert output_path.exists()
    assert schema_path.exists()
    assert summary_path.exists()
    assert summary["total_input_rows"] == 3
    assert summary["total_output_rows"] == 2
    assert summary["dropped_missing_eval_rows"] == 1
    assert summary["upset_count"] == 2
    assert summary["non_upset_count"] == 0
    assert summary["snapshot_counts_by_move"] == {"15": 1, "20": 1}
    assert json.loads(summary_path.read_text(encoding="utf-8")) == summary

    features = pd.read_parquet(output_path)
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    assert len(features) == 2
    assert schema["target_column"] == "upset_label"
    assert schema["model_input_features"]
    assert "game_id" not in schema["model_input_features"]
    assert "fen" not in schema["model_input_features"]


def _snapshot_row(
    game_id: str,
    snapshot_move: int,
    eval_cp_white_pov: int | None,
) -> dict[str, object]:
    return {
        "game_id": game_id,
        "snapshot_move": snapshot_move,
        "snapshot_ply": snapshot_move * 2,
        "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
        "side_to_move": "white",
        "white_elo": 2100,
        "black_elo": 2000,
        "result": "0-1",
        "winner_color": "black",
        "time_control": "300+0",
        "initial_time_sec": 300,
        "increment_sec": 0,
        "final_fullmove_number": 35,
        "rating_gap": 100,
        "higher_rated_color": "white",
        "lower_rated_color": "black",
        "lower_is_white": False,
        "white_clock_sec": 40,
        "black_clock_sec": 20,
        "lower_clock_sec": 20,
        "higher_clock_sec": 40,
        "upset_label": 1,
        "eval_cp_white_pov": eval_cp_white_pov,
        "eval_cp_clipped": eval_cp_white_pov,
        "mate_flag": False,
        "depth": 8,
    }
