from dataclasses import replace
from pathlib import Path

import pytest
from plyshock.parsing.filters import (
    build_upset_label,
    get_rating_context,
    get_winner_color,
    validate_game_for_plyshock,
)
from plyshock.parsing.pgn_reader import ParsedGame, read_pgn_games

SAMPLE_PGN = Path("research/data/samples/sample.pgn")


def test_validate_game_for_plyshock_accepts_sample_game() -> None:
    game = _sample_game()

    result = validate_game_for_plyshock(game, min_fullmove=13)

    assert result.accepted is True
    assert result.reason is None


def test_validate_game_for_plyshock_rejects_draw() -> None:
    game = replace(_sample_game(), result="1/2-1/2")

    result = validate_game_for_plyshock(game, min_fullmove=13)

    assert result.accepted is False
    assert result.reason == "non_decisive_result"


def test_validate_game_for_plyshock_rejects_invalid_rating() -> None:
    game = replace(_sample_game(), white_elo=0)

    result = validate_game_for_plyshock(game, min_fullmove=13)

    assert result.accepted is False
    assert result.reason == "invalid_rating"


def test_validate_game_for_plyshock_rejects_small_rating_gap() -> None:
    game = replace(_sample_game(), black_elo=2050)

    result = validate_game_for_plyshock(game, min_fullmove=13)

    assert result.accepted is False
    assert result.reason == "rating_gap_too_small"


def test_validate_game_for_plyshock_rejects_short_game() -> None:
    game = _sample_game()

    result = validate_game_for_plyshock(game)

    assert result.accepted is False
    assert result.reason == "game_too_short"


def test_validate_game_for_plyshock_rejects_missing_time_control() -> None:
    game = replace(_sample_game(), time_control="-")

    result = validate_game_for_plyshock(game, min_fullmove=13)

    assert result.accepted is False
    assert result.reason == "missing_time_control"


def test_validate_game_for_plyshock_rejects_invalid_initial_time() -> None:
    game = replace(_sample_game(), initial_time_sec=0)

    result = validate_game_for_plyshock(game, min_fullmove=13)

    assert result.accepted is False
    assert result.reason == "invalid_initial_time"


def test_validate_game_for_plyshock_rejects_missing_moves() -> None:
    game = replace(_sample_game(), moves_san=[], fens_after_move=[], clock_by_ply=[])

    result = validate_game_for_plyshock(game, min_fullmove=13)

    assert result.accepted is False
    assert result.reason == "missing_moves"


def test_validate_game_for_plyshock_rejects_missing_clocks() -> None:
    game = _sample_game()
    game_without_clocks = replace(game, clock_by_ply=[None] * len(game.moves_san))

    result = validate_game_for_plyshock(game_without_clocks, min_fullmove=13)

    assert result.accepted is False
    assert result.reason == "missing_clocks"


def test_validate_game_for_plyshock_rejects_length_mismatch() -> None:
    game = _sample_game()
    mismatched_game = replace(game, fens_after_move=game.fens_after_move[:-1])

    result = validate_game_for_plyshock(mismatched_game, min_fullmove=13)

    assert result.accepted is False
    assert result.reason == "length_mismatch"


@pytest.mark.parametrize(
    ("result", "expected"),
    [
        ("1-0", "white"),
        ("0-1", "black"),
    ],
)
def test_get_winner_color(result: str, expected: str) -> None:
    assert get_winner_color(result) == expected


def test_get_winner_color_rejects_draw() -> None:
    with pytest.raises(ValueError, match="not decisive"):
        get_winner_color("1/2-1/2")


def test_get_rating_context() -> None:
    assert get_rating_context(2100, 2000) == {
        "rating_gap": 100,
        "higher_rated_color": "white",
        "lower_rated_color": "black",
        "lower_is_white": False,
    }


@pytest.mark.parametrize(
    ("result", "white_elo", "black_elo", "expected"),
    [
        ("0-1", 2100, 2000, 1),
        ("1-0", 2100, 2000, 0),
        ("1-0", 1900, 2000, 1),
        ("0-1", 1900, 2000, 0),
    ],
)
def test_build_upset_label(
    result: str, white_elo: int, black_elo: int, expected: int
) -> None:
    assert build_upset_label(result, white_elo, black_elo) == expected


@pytest.mark.parametrize(
    ("result", "white_elo", "black_elo"),
    [
        ("1/2-1/2", 2100, 2000),
        ("1-0", 2000, 2000),
    ],
)
def test_build_upset_label_rejects_non_decisive_or_equal_ratings(
    result: str, white_elo: int, black_elo: int
) -> None:
    with pytest.raises(ValueError):
        build_upset_label(result, white_elo, black_elo)


def _sample_game() -> ParsedGame:
    return read_pgn_games(SAMPLE_PGN, max_games=1)[0]
