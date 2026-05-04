import json
from pathlib import Path

import pandas as pd
from plyshock.pipelines.build_snapshots import build_snapshots_dataset


def test_build_snapshots_dataset_writes_parquet_and_summary(tmp_path: Path) -> None:
    input_path = tmp_path / "filtered_games.parquet"
    output_path = tmp_path / "snapshots.parquet"
    summary_path = tmp_path / "summary.json"
    pd.DataFrame([_game_record("game-35", 35), _game_record("game-20", 20)]).to_parquet(
        input_path, index=False
    )

    summary = build_snapshots_dataset(input_path, output_path, summary_path)

    assert output_path.exists()
    assert summary_path.exists()
    assert summary["total_games"] == 2
    assert summary["total_snapshots"] == 7
    assert summary["snapshot_moves"] == [15, 20, 25, 30, 35]
    assert summary["snapshot_counts_by_move"] == {
        "15": 2,
        "20": 2,
        "25": 1,
        "30": 1,
        "35": 1,
    }
    assert summary["games_with_zero_snapshots"] == 0
    assert summary["upset_snapshot_count"] == 7
    assert summary["non_upset_snapshot_count"] == 0
    assert json.loads(summary_path.read_text(encoding="utf-8")) == summary

    snapshots = pd.read_parquet(output_path)
    assert len(snapshots) == 7
    assert set(snapshots["game_id"]) == {"game-35", "game-20"}
    assert snapshots.loc[0, "fen"]


def _game_record(game_id: str, final_fullmove_number: int) -> dict[str, object]:
    ply_count = final_fullmove_number * 2
    return {
        "game_id": game_id,
        "site": f"https://lichess.org/{game_id}",
        "white_elo": 2100,
        "black_elo": 2000,
        "result": "0-1",
        "winner_color": "black",
        "time_control": "300+0",
        "initial_time_sec": 300,
        "increment_sec": 0,
        "final_fullmove_number": final_fullmove_number,
        "moves_san": ["e4"] * ply_count,
        "fens_after_move": [_fen_after_ply(ply) for ply in range(1, ply_count + 1)],
        "clock_by_ply": [1000 - ply for ply in range(1, ply_count + 1)],
        "rating_gap": 100,
        "higher_rated_color": "white",
        "lower_rated_color": "black",
        "lower_is_white": False,
        "upset_label": 1,
    }


def _fen_after_ply(ply: int) -> str:
    active_color = "b" if ply % 2 == 1 else "w"
    return f"8/8/8/8/8/8/8/8 {active_color} - - 0 1"
