"""PGN replay analysis for the PlyShock demo backend."""

from __future__ import annotations

from dataclasses import asdict
from io import StringIO
from math import tanh
from pathlib import Path
from typing import Any

import chess
import chess.pgn
import pandas as pd
from plyshock.engine.stockfish_client import evaluate_fens
from plyshock.features.feature_pipeline import build_feature_dataframe
from plyshock.features.snapshot_builder import build_snapshots_from_game_record
from plyshock.parsing.clock_parser import extract_clock_comment
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


def summarize_pgn_text(pgn_text: str) -> dict[str, object]:
    """Return lightweight demo-game metadata without engine or model work."""
    parsed_game = _parse_pgn_text(pgn_text)
    game_record = _build_game_record(parsed_game)
    return {
        "label": _build_game_label(parsed_game),
        "white_elo": parsed_game.white_elo,
        "black_elo": parsed_game.black_elo,
        "result": parsed_game.result,
        "rating_gap": game_record["rating_gap"],
        "lower_rated_color": game_record["lower_rated_color"],
        "actual_upset_label": game_record["upset_label"],
    }


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
    _validate_artifact_paths(
        model_path=model_path,
        schema_path=schema_path,
        stockfish_path=stockfish_path,
    )
    _validate_depth(depth, "Stockfish depth")
    _validate_moves(snapshot_moves, "snapshot_moves")

    parsed_game = _parse_pgn_text(pgn_text)
    game_record = _validate_and_build_game_record(parsed_game)
    snapshots = _predict_checkpoint_snapshots(
        game_record=game_record,
        depth=depth,
        snapshot_moves=snapshot_moves,
        model_path=model_path,
        schema_path=schema_path,
        stockfish_path=stockfish_path,
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


def analyze_pgn_replay_text(
    *,
    pgn_text: str,
    eval_depth: int,
    prediction_depth: int,
    checkpoint_moves: list[int],
    max_plies: int,
    model_path: Path,
    schema_path: Path,
    stockfish_path: Path,
) -> dict[str, Any]:
    """Analyze a PGN and return full replay rows with checkpoint PlyShock predictions."""
    _validate_artifact_paths(
        model_path=model_path,
        schema_path=schema_path,
        stockfish_path=stockfish_path,
    )
    _validate_depth(eval_depth, "eval_depth")
    _validate_depth(prediction_depth, "prediction_depth")
    _validate_moves(checkpoint_moves, "checkpoint_moves")
    if max_plies < 0:
        raise DemoAnalysisError(400, "max_plies must be greater than or equal to 0.")

    chess_game = _read_chess_game(pgn_text)
    try:
        parsed_game = parse_single_game(chess_game)
    except ValueError as error:
        raise DemoAnalysisError(400, f"Invalid PGN: {error}") from error

    game_record = _validate_and_build_game_record(parsed_game)
    replay_moves = _build_replay_moves(chess_game, max_plies=max_plies)
    if not replay_moves:
        raise DemoAnalysisError(400, "No replay moves were generated.")

    try:
        replay_evaluations = evaluate_fens(
            stockfish_path,
            [str(row["fen"]) for row in replay_moves],
            depth=eval_depth,
        )
    except Exception as error:
        raise DemoAnalysisError(503, f"Stockfish evaluation failed: {error}") from error

    for row, evaluation in zip(replay_moves, replay_evaluations, strict=True):
        eval_cp = int(evaluation.eval_cp_white_pov)
        row["stockfish_eval_cp_white_pov"] = eval_cp
        row["stockfish_bar"] = float(tanh(eval_cp / 400))

    checkpoint_snapshots = _predict_checkpoint_snapshots(
        game_record=game_record,
        depth=prediction_depth,
        snapshot_moves=checkpoint_moves,
        model_path=model_path,
        schema_path=schema_path,
        stockfish_path=stockfish_path,
    )
    checkpoints_by_ply = {
        int(snapshot["snapshot_ply"]): snapshot for snapshot in checkpoint_snapshots
    }

    for row in replay_moves:
        checkpoint = checkpoints_by_ply.get(int(row["ply"]))
        row["is_checkpoint"] = checkpoint is not None
        row["checkpoint_move"] = (
            int(checkpoint["snapshot_move"]) if checkpoint is not None else None
        )
        row["plyshock"] = _build_plyshock_payload(checkpoint) if checkpoint else None

    checkpoints = [
        {
            "snapshot_move": int(snapshot["snapshot_move"]),
            "ply": int(snapshot["snapshot_ply"]),
            "fen": snapshot["fen"],
            "upset_probability": snapshot["upset_probability"],
            "predicted_label": int(snapshot["predicted_label"]),
            "eval_cp_lower_pov": float(snapshot["eval_cp_lower_pov"]),
        }
        for snapshot in checkpoint_snapshots
    ]

    returned_plies = min(len(parsed_game.moves_san), max_plies)
    return {
        "metadata": _build_replay_metadata(parsed_game, game_record),
        "moves": replay_moves,
        "checkpoints": checkpoints,
        "summary": {
            "total_plies": len(parsed_game.moves_san),
            "returned_plies": returned_plies,
            "checkpoint_count": len(checkpoints),
            "eval_depth": eval_depth,
            "prediction_depth": prediction_depth,
            "model_name": "best_model",
        },
    }


def evaluate_live_position(
    *,
    fen: str,
    white_elo: int,
    black_elo: int,
    white_clock_sec: int | float | None,
    black_clock_sec: int | float | None,
    initial_time_sec: int | float,
    increment_sec: int | float,
    fullmove_number: int,
    ply: int,
    checkpoint_history: list[dict[str, object]],
    eval_depth: int,
    prediction_depth: int,
    model_path: Path,
    schema_path: Path,
    stockfish_path: Path,
) -> dict[str, object]:
    """Evaluate a live board and optionally return a checkpoint PlyShock prediction."""
    _validate_artifact_paths(
        model_path=model_path,
        schema_path=schema_path,
        stockfish_path=stockfish_path,
    )
    _validate_depth(eval_depth, "eval_depth")
    _validate_depth(prediction_depth, "prediction_depth")
    _validate_live_position_inputs(
        white_elo=white_elo,
        black_elo=black_elo,
        initial_time_sec=initial_time_sec,
        fullmove_number=fullmove_number,
        ply=ply,
    )
    _validate_fen(fen)

    rating_context = get_rating_context(white_elo, black_elo)
    lower_rated_color = str(rating_context["lower_rated_color"])
    higher_rated_color = str(rating_context["higher_rated_color"])
    lower_clock_sec, higher_clock_sec = _map_live_clocks(
        lower_rated_color=lower_rated_color,
        higher_rated_color=higher_rated_color,
        white_clock_sec=white_clock_sec,
        black_clock_sec=black_clock_sec,
    )

    try:
        evaluation = evaluate_fens(stockfish_path, [fen], depth=eval_depth)[0]
    except Exception as error:
        raise DemoAnalysisError(503, f"Stockfish evaluation failed: {error}") from error

    eval_cp_white_pov = int(evaluation.eval_cp_white_pov)
    is_checkpoint = _is_live_checkpoint(fullmove_number=fullmove_number, ply=ply)
    checkpoint_move = fullmove_number if is_checkpoint else None

    response: dict[str, object] = {
        "stockfish_eval_cp_white_pov": eval_cp_white_pov,
        "stockfish_bar": float(tanh(eval_cp_white_pov / 400)),
        "lower_rated_color": lower_rated_color,
        "higher_rated_color": higher_rated_color,
        "rating_gap": int(rating_context["rating_gap"]),
        "lower_clock_sec": lower_clock_sec,
        "higher_clock_sec": higher_clock_sec,
        "is_checkpoint": is_checkpoint,
        "checkpoint_move": checkpoint_move,
        "plyshock": None,
    }

    if not is_checkpoint:
        return response

    if lower_clock_sec is None or higher_clock_sec is None:
        raise DemoAnalysisError(
            400,
            "white_clock_sec and black_clock_sec are required for checkpoint predictions.",
        )

    eval_cp_lower_pov = (
        eval_cp_white_pov if lower_rated_color == "white" else -eval_cp_white_pov
    )
    feature_values = _build_live_model_features(
        rating_gap=int(rating_context["rating_gap"]),
        lower_is_white=lower_rated_color == "white",
        snapshot_move=fullmove_number,
        snapshot_ply=ply,
        initial_time_sec=float(initial_time_sec),
        increment_sec=float(increment_sec),
        lower_clock_sec=float(lower_clock_sec),
        higher_clock_sec=float(higher_clock_sec),
        eval_cp_white_pov=eval_cp_white_pov,
        eval_cp_lower_pov=eval_cp_lower_pov,
        eval_cp_clipped=int(evaluation.eval_cp_clipped),
        mate_flag=bool(evaluation.mate_flag),
        checkpoint_history=checkpoint_history,
    )

    try:
        schema = load_feature_schema(schema_path)
        model_input_features = get_model_input_features(schema)
        missing_features = [
            feature for feature in model_input_features if feature not in feature_values
        ]
        if missing_features:
            missing = ", ".join(missing_features)
            raise DemoAnalysisError(
                400,
                f"Live feature row is missing model feature(s): {missing}.",
            )

        model_features = pd.DataFrame(
            [{feature: feature_values[feature] for feature in model_input_features}],
            columns=model_input_features,
        )
        model = load_model(model_path)
        predicted_label = int(model.predict(model_features)[0])
        upset_probability = _predict_upset_probabilities(model, model_features)[0]
    except DemoAnalysisError:
        raise
    except ValueError as error:
        raise DemoAnalysisError(400, str(error)) from error
    except Exception as error:
        raise DemoAnalysisError(503, f"Model prediction failed: {error}") from error

    response["plyshock"] = {
        "upset_probability": upset_probability,
        "predicted_label": predicted_label,
        "interpretation": _interpretation(predicted_label),
        "eval_cp_lower_pov": float(eval_cp_lower_pov),
        "lower_is_better_by_engine": eval_cp_lower_pov > 0,
    }
    return response


def _predict_checkpoint_snapshots(
    *,
    game_record: dict[str, object],
    depth: int,
    snapshot_moves: list[int],
    model_path: Path,
    schema_path: Path,
    stockfish_path: Path,
) -> list[dict[str, object]]:
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

    try:
        model = load_model(model_path)
        model_features = feature_df[model_input_features]
        predicted_labels = [int(label) for label in model.predict(model_features)]
        upset_probabilities = _predict_upset_probabilities(model, model_features)
    except Exception as error:
        raise DemoAnalysisError(503, f"Model prediction failed: {error}") from error

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

    return snapshots


def _parse_pgn_text(pgn_text: str) -> ParsedGame:
    game = _read_chess_game(pgn_text)
    try:
        return parse_single_game(game)
    except ValueError as error:
        raise DemoAnalysisError(400, f"Invalid PGN: {error}") from error


def _read_chess_game(pgn_text: str) -> chess.pgn.Game:
    if not pgn_text.strip():
        raise DemoAnalysisError(400, "Invalid PGN: request body contains no PGN text.")

    game = chess.pgn.read_game(StringIO(pgn_text))
    if game is None:
        raise DemoAnalysisError(400, "Invalid PGN: no game found.")
    if game.errors:
        first_error = game.errors[0]
        raise DemoAnalysisError(400, f"Invalid PGN: {first_error}")

    return game


def _validate_artifact_paths(*, model_path: Path, schema_path: Path, stockfish_path: Path) -> None:
    if not model_path.exists():
        raise DemoAnalysisError(503, f"Model artifact not found: {model_path}")
    if not schema_path.exists():
        raise DemoAnalysisError(503, f"Feature schema file not found: {schema_path}")
    if not stockfish_path.exists():
        raise DemoAnalysisError(503, f"Stockfish executable not found: {stockfish_path}")


def _validate_depth(depth: int, name: str) -> None:
    if depth <= 0:
        raise DemoAnalysisError(400, f"{name} must be a positive integer.")


def _validate_moves(moves: list[int], name: str) -> None:
    if not moves:
        raise DemoAnalysisError(400, f"{name} must include at least one move number.")
    if any(move <= 0 for move in moves):
        raise DemoAnalysisError(400, f"{name} must contain positive move numbers.")


def _validate_fen(fen: str) -> None:
    try:
        board = chess.Board(fen)
    except ValueError as error:
        raise DemoAnalysisError(400, f"Invalid FEN: {error}") from error

    if not board.is_valid():
        raise DemoAnalysisError(400, "Invalid FEN: position is not a valid chess board state.")


def _validate_live_position_inputs(
    *,
    white_elo: int,
    black_elo: int,
    initial_time_sec: int | float,
    fullmove_number: int,
    ply: int,
) -> None:
    if white_elo <= 0 or black_elo <= 0:
        raise DemoAnalysisError(400, "white_elo and black_elo must be positive integers.")
    if white_elo == black_elo:
        raise DemoAnalysisError(400, "Live upset prediction requires a non-zero rating gap.")
    if initial_time_sec <= 0:
        raise DemoAnalysisError(400, "initial_time_sec must be greater than 0.")
    if fullmove_number <= 0:
        raise DemoAnalysisError(400, "fullmove_number must be a positive integer.")
    if ply < 0:
        raise DemoAnalysisError(400, "ply must be greater than or equal to 0.")


def _validate_and_build_game_record(game: ParsedGame) -> dict[str, object]:
    filter_result = validate_game_for_plyshock(game)
    if not filter_result.accepted:
        reason = filter_result.reason or "unknown_reason"
        raise DemoAnalysisError(400, f"PGN rejected by PlyShock filters: {reason}.")
    return _build_game_record(game)


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


def _build_replay_metadata(game: ParsedGame, record: dict[str, object]) -> dict[str, object]:
    metadata = _build_metadata(game, record)
    metadata.update(
        {
            "white": game.white,
            "black": game.black,
        }
    )
    return metadata


def _build_game_label(game: ParsedGame) -> str:
    white = game.white or "White"
    black = game.black or "Black"
    return f"{white} vs {black} ({game.result})"


def _build_replay_moves(game: chess.pgn.Game, max_plies: int) -> list[dict[str, object]]:
    board = game.board()
    rows: list[dict[str, object]] = [
        {
            "ply": 0,
            "fullmove": board.fullmove_number,
            "san": None,
            "uci": None,
            "fen": board.fen(),
            "side_to_move": _side_to_move(board),
            "white_clock_sec": None,
            "black_clock_sec": None,
            "stockfish_eval_cp_white_pov": None,
            "stockfish_bar": None,
            "is_checkpoint": False,
            "checkpoint_move": None,
            "plyshock": None,
        }
    ]

    white_clock_sec: int | None = None
    black_clock_sec: int | None = None
    node = game
    ply = 0
    while node.variations and ply < max_plies:
        next_node = node.variation(0)
        move = next_node.move
        if move is None:
            raise DemoAnalysisError(400, "Invalid PGN: mainline node is missing a move.")

        san = board.san(move)
        uci = move.uci()
        board.push(move)
        ply += 1

        clock_sec = extract_clock_comment(next_node.comment)
        if clock_sec is not None:
            if ply % 2 == 1:
                white_clock_sec = clock_sec
            else:
                black_clock_sec = clock_sec

        rows.append(
            {
                "ply": ply,
                "fullmove": (ply + 1) // 2,
                "san": san,
                "uci": uci,
                "fen": board.fen(),
                "side_to_move": _side_to_move(board),
                "white_clock_sec": white_clock_sec,
                "black_clock_sec": black_clock_sec,
                "stockfish_eval_cp_white_pov": None,
                "stockfish_bar": None,
                "is_checkpoint": False,
                "checkpoint_move": None,
                "plyshock": None,
            }
        )
        node = next_node

    return rows


def _side_to_move(board: chess.Board) -> str:
    return "white" if board.turn == chess.WHITE else "black"


def _map_live_clocks(
    *,
    lower_rated_color: str,
    higher_rated_color: str,
    white_clock_sec: int | float | None,
    black_clock_sec: int | float | None,
) -> tuple[int | float | None, int | float | None]:
    clock_by_color = {"white": white_clock_sec, "black": black_clock_sec}
    return clock_by_color[lower_rated_color], clock_by_color[higher_rated_color]


def _is_live_checkpoint(*, fullmove_number: int, ply: int) -> bool:
    if fullmove_number not in {15, 20, 25, 30, 35}:
        return False
    if fullmove_number < 15:
        return False

    expected_ply = fullmove_number * 2
    return abs(ply - expected_ply) <= 1


def _build_live_model_features(
    *,
    rating_gap: int,
    lower_is_white: bool,
    snapshot_move: int,
    snapshot_ply: int,
    initial_time_sec: float,
    increment_sec: float,
    lower_clock_sec: float,
    higher_clock_sec: float,
    eval_cp_white_pov: int,
    eval_cp_lower_pov: int,
    eval_cp_clipped: int,
    mate_flag: bool,
    checkpoint_history: list[dict[str, object]],
) -> dict[str, float | int]:
    thresholds = max(initial_time_sec * 0.10, 30)
    lower_time_pressure_flag = int(lower_clock_sec <= thresholds)
    higher_time_pressure_flag = int(higher_clock_sec <= thresholds)
    eval_history = _extract_live_eval_history(checkpoint_history)
    eval_delta, eval_trend, eval_volatility = _live_eval_trend_features(
        eval_history=eval_history,
        current_eval=eval_cp_lower_pov,
    )

    return {
        "rating_gap": rating_gap,
        "lower_is_white": int(lower_is_white),
        "snapshot_move": snapshot_move,
        "snapshot_ply": snapshot_ply,
        "initial_time_sec": initial_time_sec,
        "increment_sec": increment_sec,
        "lower_clock_sec": lower_clock_sec,
        "higher_clock_sec": higher_clock_sec,
        "clock_diff_lower_minus_higher": lower_clock_sec - higher_clock_sec,
        "lower_clock_ratio": lower_clock_sec / initial_time_sec,
        "higher_clock_ratio": higher_clock_sec / initial_time_sec,
        "lower_time_pressure_flag": lower_time_pressure_flag,
        "higher_time_pressure_flag": higher_time_pressure_flag,
        "eval_cp_white_pov": eval_cp_white_pov,
        "eval_cp_clipped": eval_cp_clipped,
        "eval_cp_lower_pov": eval_cp_lower_pov,
        "eval_abs": abs(eval_cp_lower_pov),
        "lower_is_better_by_engine": int(eval_cp_lower_pov > 0),
        "mate_flag": int(mate_flag),
        "eval_delta_from_prev_snapshot": eval_delta,
        "eval_trend_from_first_snapshot": eval_trend,
        "eval_volatility_so_far": eval_volatility,
        "large_eval_swing_flag": int(abs(eval_delta) >= 150),
        "rating_gap_x_eval_lower_pov": rating_gap * eval_cp_lower_pov,
        "higher_time_pressure_x_eval_volatility": higher_time_pressure_flag * eval_volatility,
        "lower_worse_but_higher_under_pressure": int(
            eval_cp_lower_pov < -100 and higher_time_pressure_flag == 1
        ),
    }


def _extract_live_eval_history(checkpoint_history: list[dict[str, object]]) -> list[float]:
    values: list[float] = []
    for item in checkpoint_history:
        value = item.get("eval_cp_lower_pov")
        if value is None:
            continue
        try:
            values.append(float(value))
        except (TypeError, ValueError):
            continue
    return values


def _live_eval_trend_features(
    *, eval_history: list[float], current_eval: float
) -> tuple[float, float, float]:
    if not eval_history:
        return 0.0, 0.0, 0.0

    eval_delta = current_eval - eval_history[-1]
    eval_trend = current_eval - eval_history[0]
    values = [*eval_history, float(current_eval)]
    if len(values) < 2:
        eval_volatility = 0.0
    else:
        mean = sum(values) / len(values)
        variance = sum((value - mean) ** 2 for value in values) / (len(values) - 1)
        eval_volatility = variance**0.5

    return eval_delta, eval_trend, eval_volatility


def _build_plyshock_payload(checkpoint: dict[str, object]) -> dict[str, object]:
    return {
        "upset_probability": checkpoint["upset_probability"],
        "predicted_label": int(checkpoint["predicted_label"]),
        "interpretation": checkpoint["interpretation"],
        "eval_cp_lower_pov": float(checkpoint["eval_cp_lower_pov"]),
        "lower_clock_sec": checkpoint["lower_clock_sec"],
        "higher_clock_sec": checkpoint["higher_clock_sec"],
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
