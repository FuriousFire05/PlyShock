"""PGN replay analysis for the PlyShock demo backend."""

from __future__ import annotations

from dataclasses import asdict
from io import StringIO
from pathlib import Path
from typing import Any

import chess.pgn
import pandas as pd
from plyshock.engine.stockfish_client import evaluate_fens
from plyshock.features.feature_pipeline import build_feature_dataframe
from plyshock.features.snapshot_builder import build_snapshots_from_game_record
from plyshock.parsing.filters import (
    build_upset_label,
    get_rating_context,
    get_winner_color,
    validate_game_for_plyshock,
)
from plyshock.parsing.pgn_reader import ParsedGame, parse_single_game

from app.backend.model_loader import get_model_input_features, load_feature_schema, load_model


class DemoAnalysisError(Exception):
    """Error type carrying an HTTP-friendly status and detail."""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def analyze_pgn_text(
    *,
    pgn_text: str,
    depth: int,
    snapshot_moves: list[int],
    model_path: Path,
    schema_path: Path,
    stockfish_path: Path,
) -> dict[str, Any]:
    """Analyze one PGN and return model predictions for mid-game snapshots."""
    if not model_path.exists():
        raise DemoAnalysisError(503, f"Model artifact not found: {model_path}")
    if not schema_path.exists():
        raise DemoAnalysisError(503, f"Feature schema file not found: {schema_path}")
    if not stockfish_path.exists():
        raise DemoAnalysisError(503, f"Stockfish executable not found: {stockfish_path}")
    if depth <= 0:
        raise DemoAnalysisError(400, "Stockfish depth must be a positive integer.")
    if not snapshot_moves:
        raise DemoAnalysisError(400, "snapshot_moves must include at least one move number.")
    if any(move <= 0 for move in snapshot_moves):
        raise DemoAnalysisError(400, "snapshot_moves must contain positive move numbers.")

    parsed_game = _parse_pgn_text(pgn_text)
    filter_result = validate_game_for_plyshock(parsed_game)
    if not filter_result.accepted:
        reason = filter_result.reason or "unknown_reason"
        raise DemoAnalysisError(400, f"PGN rejected by PlyShock filters: {reason}.")

    game_record = _build_game_record(parsed_game)
    snapshot_rows = build_snapshots_from_game_record(game_record, snapshot_moves=snapshot_moves)
    if not snapshot_rows:
        raise DemoAnalysisError(400, "No snapshots were generated for the requested moves.")

    fens = [str(row["fen"]) for row in snapshot_rows]
    try:
        evaluations = evaluate_fens(stockfish_path, fens, depth=depth)
    except Exception as error:
        raise DemoAnalysisError(503, f"Stockfish evaluation failed: {error}") from error

    evaluated_rows = []
    for row, evaluation in zip(snapshot_rows, evaluations, strict=True):
        evaluated_row = row.copy()
        evaluated_row.update(
            {
                "eval_cp_white_pov": evaluation.eval_cp_white_pov,
                "eval_cp_clipped": evaluation.eval_cp_clipped,
                "mate_flag": evaluation.mate_flag,
                "depth": evaluation.depth if evaluation.depth is not None else depth,
            }
        )
        evaluated_rows.append(evaluated_row)

    try:
        feature_df = build_feature_dataframe(pd.DataFrame(evaluated_rows))
        schema = load_feature_schema(schema_path)
        model_input_features = get_model_input_features(schema)
    except ValueError as error:
        raise DemoAnalysisError(400, str(error)) from error

    missing_features = [feature for feature in model_input_features if feature not in feature_df]
    if missing_features:
        missing = ", ".join(missing_features)
        raise DemoAnalysisError(400, f"Feature dataframe is missing model feature(s): {missing}.")

    model = load_model(model_path)
    model_features = feature_df[model_input_features]
    predicted_labels = [int(label) for label in model.predict(model_features)]
    upset_probabilities = _predict_upset_probabilities(model, model_features)

    snapshots = []
    for index, row in enumerate(evaluated_rows):
        feature_row = feature_df.iloc[index]
        predicted_label = predicted_labels[index]
        snapshots.append(
            {
                "snapshot_move": int(row["snapshot_move"]),
                "snapshot_ply": int(row["snapshot_ply"]),
                "fen": row["fen"],
                "side_to_move": row["side_to_move"],
                "white_clock_sec": _none_if_missing(row["white_clock_sec"]),
                "black_clock_sec": _none_if_missing(row["black_clock_sec"]),
                "lower_clock_sec": _none_if_missing(row["lower_clock_sec"]),
                "higher_clock_sec": _none_if_missing(row["higher_clock_sec"]),
                "eval_cp_white_pov": int(row["eval_cp_white_pov"]),
                "eval_cp_lower_pov": float(feature_row["eval_cp_lower_pov"]),
                "upset_probability": upset_probabilities[index],
                "predicted_label": predicted_label,
                "interpretation": _interpretation(predicted_label),
            }
        )

    return {
        "metadata": _build_metadata(parsed_game, game_record),
        "snapshots": snapshots,
        "summary": {
            "snapshot_count": len(snapshots),
            "model_name": "best_model",
            "stockfish_depth": depth,
        },
    }


def _parse_pgn_text(pgn_text: str) -> ParsedGame:
    if not pgn_text.strip():
        raise DemoAnalysisError(400, "Invalid PGN: request body contains no PGN text.")

    game = chess.pgn.read_game(StringIO(pgn_text))
    if game is None:
        raise DemoAnalysisError(400, "Invalid PGN: no game found.")
    if game.errors:
        first_error = game.errors[0]
        raise DemoAnalysisError(400, f"Invalid PGN: {first_error}")

    try:
        return parse_single_game(game)
    except ValueError as error:
        raise DemoAnalysisError(400, f"Invalid PGN: {error}") from error


def _build_game_record(game: ParsedGame) -> dict[str, object]:
    rating_context = get_rating_context(game.white_elo, game.black_elo)
    winner_color = get_winner_color(game.result)
    upset_label = build_upset_label(game.result, game.white_elo, game.black_elo)

    return {
        **asdict(game),
        **rating_context,
        "winner_color": winner_color,
        "upset_label": upset_label,
    }


def _build_metadata(game: ParsedGame, record: dict[str, object]) -> dict[str, object]:
    return {
        "game_id": game.game_id,
        "white_elo": game.white_elo,
        "black_elo": game.black_elo,
        "result": game.result,
        "winner_color": record["winner_color"],
        "rating_gap": record["rating_gap"],
        "higher_rated_color": record["higher_rated_color"],
        "lower_rated_color": record["lower_rated_color"],
        "actual_upset_label": record["upset_label"],
    }


def _predict_upset_probabilities(model: Any, model_features: pd.DataFrame) -> list[float | None]:
    if not hasattr(model, "predict_proba"):
        return [None] * len(model_features)

    probabilities = model.predict_proba(model_features)
    classes = getattr(model, "classes_", None)
    if classes is not None and 1 in classes:
        class_index = list(classes).index(1)
    else:
        class_index = 1 if probabilities.shape[1] > 1 else 0

    return [float(row[class_index]) for row in probabilities]


def _interpretation(predicted_label: int) -> str:
    if predicted_label == 1:
        return "Model predicts an upset."
    return "Model predicts a non-upset."


def _none_if_missing(value: object) -> object:
    if pd.isna(value):
        return None
    return value
