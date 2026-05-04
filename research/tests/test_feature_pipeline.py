import json
from pathlib import Path

import pandas as pd
import pytest
from plyshock.features.feature_pipeline import (
    LEAKAGE_EXCLUDED_COLUMNS,
    METADATA_COLUMNS,
    MODEL_INPUT_FEATURES,
    TARGET_COLUMN,
    build_feature_dataframe,
    write_feature_schema,
)


def test_eval_cp_lower_pov_flips_for_black_lower_rated_player() -> None:
    features = build_feature_dataframe(_snapshot_dataframe())

    game_one = features[features["game_id"] == "game-1"].reset_index(drop=True)

    assert game_one.loc[0, "eval_cp_lower_pov"] == -100
    assert game_one.loc[1, "eval_cp_lower_pov"] == -250


def test_clock_ratios_and_time_pressure_flags_work() -> None:
    features = build_feature_dataframe(_snapshot_dataframe())
    first_snapshot = features[features["game_id"] == "game-1"].iloc[0]
    second_snapshot = features[features["game_id"] == "game-1"].iloc[1]

    assert first_snapshot["lower_clock_ratio"] == pytest.approx(20 / 300)
    assert first_snapshot["higher_clock_ratio"] == pytest.approx(40 / 300)
    assert first_snapshot["lower_time_pressure_flag"] == 1
    assert first_snapshot["higher_time_pressure_flag"] == 0
    assert second_snapshot["higher_time_pressure_flag"] == 1


def test_first_snapshot_delta_and_volatility_are_zero() -> None:
    features = build_feature_dataframe(_snapshot_dataframe())
    first_snapshot = features[features["game_id"] == "game-1"].iloc[0]

    assert first_snapshot["eval_delta_from_prev_snapshot"] == 0
    assert first_snapshot["eval_trend_from_first_snapshot"] == 0
    assert first_snapshot["eval_volatility_so_far"] == 0


def test_later_snapshot_history_features_use_previous_snapshots_only() -> None:
    features = build_feature_dataframe(_snapshot_dataframe())
    second_snapshot = features[features["game_id"] == "game-1"].iloc[1]

    assert second_snapshot["eval_delta_from_prev_snapshot"] == -150
    assert second_snapshot["eval_trend_from_first_snapshot"] == -150
    assert second_snapshot["eval_volatility_so_far"] == pytest.approx(106.066017, rel=1e-6)
    assert second_snapshot["large_eval_swing_flag"] == 1
    assert second_snapshot["rating_gap_x_eval_lower_pov"] == -25000
    assert second_snapshot["higher_time_pressure_x_eval_volatility"] == pytest.approx(
        106.066017, rel=1e-6
    )
    assert second_snapshot["lower_worse_but_higher_under_pressure"] == 1


def test_white_lower_rated_player_keeps_white_eval_perspective() -> None:
    features = build_feature_dataframe(_snapshot_dataframe())
    game_two = features[features["game_id"] == "game-2"].iloc[0]

    assert game_two["eval_cp_lower_pov"] == 80
    assert game_two["lower_is_better_by_engine"] == 1


def test_leakage_columns_are_not_model_input_features(tmp_path: Path) -> None:
    schema_path = tmp_path / "feature_schema.json"

    write_feature_schema(schema_path, MODEL_INPUT_FEATURES, METADATA_COLUMNS, TARGET_COLUMN)

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    assert set(LEAKAGE_EXCLUDED_COLUMNS).isdisjoint(schema["model_input_features"])
    assert schema["target_column"] == "upset_label"


def _snapshot_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        [
            _snapshot_row(
                game_id="game-1",
                snapshot_move=15,
                lower_rated_color="black",
                higher_rated_color="white",
                lower_is_white=False,
                lower_clock_sec=20,
                higher_clock_sec=40,
                eval_cp_white_pov=100,
            ),
            _snapshot_row(
                game_id="game-1",
                snapshot_move=20,
                lower_rated_color="black",
                higher_rated_color="white",
                lower_is_white=False,
                lower_clock_sec=15,
                higher_clock_sec=25,
                eval_cp_white_pov=250,
            ),
            _snapshot_row(
                game_id="game-2",
                snapshot_move=15,
                lower_rated_color="white",
                higher_rated_color="black",
                lower_is_white=True,
                lower_clock_sec=100,
                higher_clock_sec=95,
                eval_cp_white_pov=80,
            ),
        ]
    )


def _snapshot_row(
    *,
    game_id: str,
    snapshot_move: int,
    lower_rated_color: str,
    higher_rated_color: str,
    lower_is_white: bool,
    lower_clock_sec: int,
    higher_clock_sec: int,
    eval_cp_white_pov: int,
) -> dict[str, object]:
    return {
        "game_id": game_id,
        "snapshot_move": snapshot_move,
        "snapshot_ply": snapshot_move * 2,
        "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
        "side_to_move": "white",
        "white_elo": 2100 if not lower_is_white else 2000,
        "black_elo": 2000 if not lower_is_white else 2100,
        "result": "0-1",
        "winner_color": "black",
        "time_control": "300+0",
        "initial_time_sec": 300,
        "increment_sec": 0,
        "final_fullmove_number": 35,
        "rating_gap": 100,
        "higher_rated_color": higher_rated_color,
        "lower_rated_color": lower_rated_color,
        "lower_is_white": lower_is_white,
        "white_clock_sec": higher_clock_sec if not lower_is_white else lower_clock_sec,
        "black_clock_sec": lower_clock_sec if not lower_is_white else higher_clock_sec,
        "lower_clock_sec": lower_clock_sec,
        "higher_clock_sec": higher_clock_sec,
        "upset_label": 1,
        "eval_cp_white_pov": eval_cp_white_pov,
        "eval_cp_clipped": eval_cp_white_pov,
        "mate_flag": False,
        "depth": 8,
    }
