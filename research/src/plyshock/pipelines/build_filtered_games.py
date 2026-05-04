"""Build a filtered PlyShock games dataset from PGN or PGN.ZST input."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Sequence

import pandas as pd

from plyshock.parsing.filters import (
    build_upset_label,
    get_rating_context,
    get_winner_color,
    validate_game_for_plyshock,
)
from plyshock.parsing.pgn_reader import ParsedGame
from plyshock.parsing.zst_reader import read_pgn_games_streaming

RECORD_COLUMNS = [
    "game_id",
    "site",
    "event",
    "utc_date",
    "white",
    "black",
    "white_elo",
    "black_elo",
    "result",
    "winner_color",
    "time_control",
    "initial_time_sec",
    "increment_sec",
    "final_fullmove_number",
    "termination",
    "moves_san",
    "fens_after_move",
    "clock_by_ply",
    "rating_gap",
    "higher_rated_color",
    "lower_rated_color",
    "lower_is_white",
    "upset_label",
]


def parsed_game_to_record(game: ParsedGame) -> dict[str, object]:
    """Convert an accepted parsed game into a tabular dataset record.

    Args:
        game: Parsed game to serialize.

    Returns:
        Dictionary containing game metadata, move arrays, rating context, and labels.
    """
    rating_context = get_rating_context(game.white_elo, game.black_elo)
    return {
        "game_id": game.game_id,
        "site": game.site,
        "event": game.event,
        "utc_date": game.utc_date,
        "white": game.white,
        "black": game.black,
        "white_elo": game.white_elo,
        "black_elo": game.black_elo,
        "result": game.result,
        "winner_color": get_winner_color(game.result),
        "time_control": game.time_control,
        "initial_time_sec": game.initial_time_sec,
        "increment_sec": game.increment_sec,
        "final_fullmove_number": game.final_fullmove_number,
        "termination": game.termination,
        "moves_san": game.moves_san,
        "fens_after_move": game.fens_after_move,
        "clock_by_ply": game.clock_by_ply,
        "rating_gap": rating_context["rating_gap"],
        "higher_rated_color": rating_context["higher_rated_color"],
        "lower_rated_color": rating_context["lower_rated_color"],
        "lower_is_white": rating_context["lower_is_white"],
        "upset_label": build_upset_label(game.result, game.white_elo, game.black_elo),
    }


def build_filtered_games(
    input_path: str | Path,
    output_path: str | Path,
    summary_path: str | Path,
    max_games: int | None = None,
    min_rating_gap: int = 100,
    min_fullmove: int = 15,
) -> dict[str, object]:
    """Build a filtered parquet dataset and JSON summary from PGN input.

    Args:
        input_path: Source ``.pgn`` or ``.pgn.zst`` file.
        output_path: Destination parquet path for accepted games.
        summary_path: Destination JSON summary path.
        max_games: Maximum parsed games to process. ``None`` processes all valid parsed games.
        min_rating_gap: Minimum absolute rating gap for acceptance.
        min_fullmove: Minimum final fullmove number for acceptance.

    Returns:
        The summary dictionary written to ``summary_path``.
    """
    source_path = Path(input_path)
    parquet_path = Path(output_path)
    report_path = Path(summary_path)

    parsed_games = read_pgn_games_streaming(source_path, max_games=max_games)
    records: list[dict[str, object]] = []
    rejection_reasons: Counter[str] = Counter()
    upset_count = 0
    non_upset_count = 0

    for game in parsed_games:
        filter_result = validate_game_for_plyshock(
            game, min_rating_gap=min_rating_gap, min_fullmove=min_fullmove
        )
        if not filter_result.accepted:
            reason = filter_result.reason or "unknown"
            rejection_reasons[reason] += 1
            continue

        record = parsed_game_to_record(game)
        records.append(record)
        if record["upset_label"] == 1:
            upset_count += 1
        else:
            non_upset_count += 1

    _write_parquet(records, parquet_path)

    summary: dict[str, object] = {
        "input_path": str(source_path),
        "output_path": str(parquet_path),
        "max_games": max_games,
        "min_rating_gap": min_rating_gap,
        "min_fullmove": min_fullmove,
        "parsed_games": len(parsed_games),
        "accepted_games": len(records),
        "rejected_games": sum(rejection_reasons.values()),
        "rejection_reasons": dict(sorted(rejection_reasons.items())),
        "upset_count": upset_count,
        "non_upset_count": non_upset_count,
    }
    _write_summary(summary, report_path)
    return summary


def main(argv: Sequence[str] | None = None) -> None:
    """Run the filtered-games pipeline from the command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Input .pgn or .pgn.zst file.")
    parser.add_argument("--output", required=True, type=Path, help="Output parquet dataset path.")
    parser.add_argument("--summary", required=True, type=Path, help="Output JSON summary path.")
    parser.add_argument(
        "--max-games", default=None, type=int, help="Maximum parsed games to process."
    )
    parser.add_argument("--min-rating-gap", default=100, type=int, help="Minimum rating gap.")
    parser.add_argument(
        "--min-fullmove", default=15, type=int, help="Minimum final fullmove number."
    )
    args = parser.parse_args(argv)

    build_filtered_games(
        input_path=args.input,
        output_path=args.output,
        summary_path=args.summary,
        max_games=args.max_games,
        min_rating_gap=args.min_rating_gap,
        min_fullmove=args.min_fullmove,
    )


def _write_parquet(records: list[dict[str, object]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    dataframe = pd.DataFrame.from_records(records, columns=RECORD_COLUMNS)
    dataframe.to_parquet(output_path, index=False)


def _write_summary(summary: dict[str, object], summary_path: Path) -> None:
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
