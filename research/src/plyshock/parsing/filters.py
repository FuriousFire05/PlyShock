"""Filtering helpers for parsed PlyShock Lichess games."""

from __future__ import annotations

from dataclasses import dataclass

from plyshock.parsing.pgn_reader import ParsedGame


@dataclass(frozen=True)
class FilterResult:
    """Outcome of validating whether a parsed game belongs in the dataset."""

    accepted: bool
    reason: str | None


def validate_game_for_plyshock(
    game: ParsedGame, min_rating_gap: int = 100, min_fullmove: int = 15
) -> FilterResult:
    """Validate a parsed game against PlyShock dataset inclusion rules.

    Args:
        game: Parsed game to validate.
        min_rating_gap: Minimum absolute rating difference required.
        min_fullmove: Minimum final fullmove number required.

    Returns:
        A ``FilterResult`` with ``accepted=True`` or a stable rejection reason.
    """
    if game.result not in {"1-0", "0-1"}:
        return FilterResult(False, "non_decisive_result")

    if not _is_valid_rating(game.white_elo) or not _is_valid_rating(game.black_elo):
        return FilterResult(False, "invalid_rating")

    if abs(game.white_elo - game.black_elo) < min_rating_gap:
        return FilterResult(False, "rating_gap_too_small")

    if game.final_fullmove_number < min_fullmove:
        return FilterResult(False, "game_too_short")

    if game.time_control in {"", "-"}:
        return FilterResult(False, "missing_time_control")

    if game.initial_time_sec <= 0:
        return FilterResult(False, "invalid_initial_time")

    if not game.moves_san:
        return FilterResult(False, "missing_moves")

    if len(game.fens_after_move) != len(game.moves_san) or len(game.clock_by_ply) != len(
        game.moves_san
    ):
        return FilterResult(False, "length_mismatch")

    if all(clock is None for clock in game.clock_by_ply):
        return FilterResult(False, "missing_clocks")

    return FilterResult(True, None)


def get_winner_color(result: str) -> str:
    """Return the winning color for a decisive PGN result.

    Args:
        result: PGN result string.

    Returns:
        ``"white"`` for ``"1-0"`` and ``"black"`` for ``"0-1"``.

    Raises:
        ValueError: If the result is not decisive.
    """
    if result == "1-0":
        return "white"
    if result == "0-1":
        return "black"
    raise ValueError(f"Result {result!r} is not decisive.")


def get_rating_context(white_elo: int, black_elo: int) -> dict[str, object]:
    """Build rating-derived context for a game.

    Args:
        white_elo: White player rating.
        black_elo: Black player rating.

    Returns:
        Rating gap, higher/lower rated colors, and whether the lower-rated player is white.

    Raises:
        ValueError: If ratings are invalid or equal.
    """
    if not _is_valid_rating(white_elo) or not _is_valid_rating(black_elo):
        raise ValueError("Ratings must be positive integers.")
    if white_elo == black_elo:
        raise ValueError("Ratings must not be equal.")

    lower_rated_color = "white" if white_elo < black_elo else "black"
    higher_rated_color = "black" if lower_rated_color == "white" else "white"
    return {
        "rating_gap": abs(white_elo - black_elo),
        "higher_rated_color": higher_rated_color,
        "lower_rated_color": lower_rated_color,
        "lower_is_white": lower_rated_color == "white",
    }


def build_upset_label(result: str, white_elo: int, black_elo: int) -> int:
    """Build a binary label indicating whether the lower-rated player won.

    Args:
        result: Decisive PGN result string.
        white_elo: White player rating.
        black_elo: Black player rating.

    Returns:
        ``1`` for an upset and ``0`` when the higher-rated player wins.

    Raises:
        ValueError: If the result is non-decisive or ratings are equal/invalid.
    """
    winner_color = get_winner_color(result)
    rating_context = get_rating_context(white_elo, black_elo)
    return int(winner_color == rating_context["lower_rated_color"])


def _is_valid_rating(value: object) -> bool:
    return type(value) is int and value > 0
