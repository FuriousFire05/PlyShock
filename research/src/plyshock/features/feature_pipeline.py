"""Feature engineering utilities for evaluated snapshot rows."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

REQUIRED_INPUT_COLUMNS = {
    "game_id",
    "snapshot_move",
    "snapshot_ply",
    "fen",
    "side_to_move",
    "white_elo",
    "black_elo",
    "result",
    "winner_color",
    "time_control",
    "initial_time_sec",
    "increment_sec",
    "final_fullmove_number",
    "rating_gap",
    "higher_rated_color",
    "lower_rated_color",
    "lower_is_white",
    "white_clock_sec",
    "black_clock_sec",
    "lower_clock_sec",
    "higher_clock_sec",
    "upset_label",
    "eval_cp_white_pov",
    "eval_cp_clipped",
    "mate_flag",
    "depth",
}

MODEL_INPUT_FEATURES = [
    "rating_gap",
    "lower_is_white",
    "snapshot_move",
    "snapshot_ply",
    "initial_time_sec",
    "increment_sec",
    "lower_clock_sec",
    "higher_clock_sec",
    "clock_diff_lower_minus_higher",
    "lower_clock_ratio",
    "higher_clock_ratio",
    "lower_time_pressure_flag",
    "higher_time_pressure_flag",
    "eval_cp_white_pov",
    "eval_cp_clipped",
    "eval_cp_lower_pov",
    "eval_abs",
    "lower_is_better_by_engine",
    "mate_flag",
    "eval_delta_from_prev_snapshot",
    "eval_trend_from_first_snapshot",
    "eval_volatility_so_far",
    "large_eval_swing_flag",
    "rating_gap_x_eval_lower_pov",
    "higher_time_pressure_x_eval_volatility",
    "lower_worse_but_higher_under_pressure",
]

TARGET_COLUMN = "upset_label"
LEAKAGE_EXCLUDED_COLUMNS = [
    "result",
    "winner_color",
    "final_fullmove_number",
    "time_control",
    "fen",
    "game_id",
]
METADATA_COLUMNS = [
    "game_id",
    "fen",
    "side_to_move",
    "white_elo",
    "black_elo",
    "result",
    "winner_color",
    "time_control",
    "final_fullmove_number",
    "higher_rated_color",
    "lower_rated_color",
    "white_clock_sec",
    "black_clock_sec",
    "depth",
]
FEATURE_COLUMNS = METADATA_COLUMNS + MODEL_INPUT_FEATURES + [TARGET_COLUMN]


def build_feature_dataframe(snapshot_df: pd.DataFrame) -> pd.DataFrame:
    """Build an ML-ready feature dataframe from evaluated snapshot rows.

    Args:
        snapshot_df: Evaluated snapshot dataframe.

    Returns:
        Feature dataframe with metadata, model input features, and target column.

    Raises:
        ValueError: If required columns are missing.
    """
    _validate_required_columns(snapshot_df)
    dataframe = snapshot_df.copy()
    dataframe = dataframe.sort_values(["game_id", "snapshot_move"]).reset_index(drop=True)

    _coerce_numeric_columns(dataframe)
    dataframe["lower_is_white"] = dataframe["lower_is_white"].astype(int)
    dataframe["mate_flag"] = dataframe["mate_flag"].astype(int)

    lower_is_white = dataframe["lower_rated_color"] == "white"
    dataframe["eval_cp_lower_pov"] = dataframe["eval_cp_white_pov"].where(
        lower_is_white, -dataframe["eval_cp_white_pov"]
    )
    dataframe["eval_abs"] = dataframe["eval_cp_lower_pov"].abs()
    dataframe["lower_is_better_by_engine"] = (dataframe["eval_cp_lower_pov"] > 0).astype(int)

    dataframe["clock_diff_lower_minus_higher"] = (
        dataframe["lower_clock_sec"] - dataframe["higher_clock_sec"]
    )
    dataframe["lower_clock_ratio"] = _clock_ratio(
        dataframe["lower_clock_sec"], dataframe["initial_time_sec"]
    )
    dataframe["higher_clock_ratio"] = _clock_ratio(
        dataframe["higher_clock_sec"], dataframe["initial_time_sec"]
    )
    thresholds = dataframe["initial_time_sec"].mul(0.10).clip(lower=30)
    dataframe["lower_time_pressure_flag"] = (
        dataframe["lower_clock_sec"].notna() & (dataframe["lower_clock_sec"] <= thresholds)
    ).astype(int)
    dataframe["higher_time_pressure_flag"] = (
        dataframe["higher_clock_sec"].notna() & (dataframe["higher_clock_sec"] <= thresholds)
    ).astype(int)

    grouped_eval = dataframe.groupby("game_id", sort=False)["eval_cp_lower_pov"]
    dataframe["eval_delta_from_prev_snapshot"] = grouped_eval.diff().fillna(0)
    dataframe["eval_trend_from_first_snapshot"] = grouped_eval.transform(
        lambda values: values - values.iloc[0]
    )
    dataframe["eval_volatility_so_far"] = grouped_eval.expanding().std().reset_index(
        level=0, drop=True
    )
    dataframe["eval_volatility_so_far"] = dataframe["eval_volatility_so_far"].fillna(0)
    dataframe["large_eval_swing_flag"] = (
        dataframe["eval_delta_from_prev_snapshot"].abs() >= 150
    ).astype(int)

    dataframe["rating_gap_x_eval_lower_pov"] = (
        dataframe["rating_gap"] * dataframe["eval_cp_lower_pov"]
    )
    dataframe["higher_time_pressure_x_eval_volatility"] = (
        dataframe["higher_time_pressure_flag"] * dataframe["eval_volatility_so_far"]
    )
    dataframe["lower_worse_but_higher_under_pressure"] = (
        (dataframe["eval_cp_lower_pov"] < -100) & (dataframe["higher_time_pressure_flag"] == 1)
    ).astype(int)

    return dataframe.reindex(columns=FEATURE_COLUMNS)


def write_feature_schema(
    path: str | Path,
    model_input_features: list[str],
    metadata_columns: list[str],
    target_column: str,
) -> None:
    """Write a JSON schema describing feature, metadata, target, and leakage columns."""
    schema_path = Path(path)
    schema_path.parent.mkdir(parents=True, exist_ok=True)
    schema = {
        "model_input_features": model_input_features,
        "metadata_columns": metadata_columns,
        "target_column": target_column,
        "leakage_excluded_columns": LEAKAGE_EXCLUDED_COLUMNS,
    }
    schema_path.write_text(json.dumps(schema, indent=2), encoding="utf-8")


def _validate_required_columns(dataframe: pd.DataFrame) -> None:
    missing_columns = REQUIRED_INPUT_COLUMNS.difference(dataframe.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Snapshot dataframe is missing required columns: {missing}.")


def _coerce_numeric_columns(dataframe: pd.DataFrame) -> None:
    numeric_columns = [
        "snapshot_move",
        "snapshot_ply",
        "white_elo",
        "black_elo",
        "initial_time_sec",
        "increment_sec",
        "final_fullmove_number",
        "rating_gap",
        "white_clock_sec",
        "black_clock_sec",
        "lower_clock_sec",
        "higher_clock_sec",
        "upset_label",
        "eval_cp_white_pov",
        "eval_cp_clipped",
        "depth",
    ]
    for column in numeric_columns:
        dataframe[column] = pd.to_numeric(dataframe[column], errors="coerce")


def _clock_ratio(clock_seconds: pd.Series, initial_time_seconds: pd.Series) -> pd.Series:
    return clock_seconds.div(initial_time_seconds.where(initial_time_seconds > 0))
