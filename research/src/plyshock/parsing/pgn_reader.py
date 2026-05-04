"""Small PGN reader utilities for Lichess sample files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import chess.pgn

from plyshock.parsing.clock_parser import extract_clock_comment, parse_time_control


@dataclass(frozen=True)
class ParsedGame:
    """Parsed metadata and mainline move data for a single Lichess PGN game."""

    game_id: str
    site: str
    event: str | None
    utc_date: str | None
    white: str | None
    black: str | None
    white_elo: int
    black_elo: int
    result: str
    time_control: str
    initial_time_sec: int
    increment_sec: int
    moves_san: list[str]
    fens_after_move: list[str]
    clock_by_ply: list[int | None]
    final_fullmove_number: int
    termination: str | None


def read_pgn_games(path: str | Path, max_games: int | None = None) -> list[ParsedGame]:
    """Read valid games from a PGN file.

    Args:
        path: PGN file path.
        max_games: Maximum number of valid games to return. ``None`` reads all games.

    Returns:
        Parsed games. Malformed games are skipped.

    Raises:
        ValueError: If ``max_games`` is negative.
    """
    if max_games is not None and max_games < 0:
        raise ValueError("max_games must be non-negative or None.")

    parsed_games: list[ParsedGame] = []
    with Path(path).open(encoding="utf-8") as pgn_file:
        while max_games is None or len(parsed_games) < max_games:
            game = chess.pgn.read_game(pgn_file)
            if game is None:
                break

            if game.errors:
                continue

            try:
                parsed_games.append(parse_single_game(game))
            except ValueError:
                continue

    return parsed_games


def parse_single_game(game: chess.pgn.Game) -> ParsedGame:
    """Parse one python-chess PGN game into a compact test-friendly structure.

    Args:
        game: A ``chess.pgn.Game`` object.

    Returns:
        Parsed metadata, SAN moves, FENs after each ply, and clock annotations.

    Raises:
        ValueError: If required Lichess headers or move annotations are invalid.
    """
    headers = game.headers
    site = _required_header(headers, "Site")
    result = _required_header(headers, "Result")
    if result not in {"1-0", "0-1", "1/2-1/2"}:
        raise ValueError(f"Invalid Result header {result!r}.")

    time_control = _required_header(headers, "TimeControl")
    initial_time_sec, increment_sec = parse_time_control(time_control)

    moves_san: list[str] = []
    fens_after_move: list[str] = []
    clock_by_ply: list[int | None] = []

    board = game.board()
    max_fullmove_number = board.fullmove_number
    node = game
    while node.variations:
        next_node = node.variation(0)
        move = next_node.move
        if move is None:
            raise ValueError("Mainline node is missing a move.")

        moves_san.append(board.san(move))
        board.push(move)
        fens_after_move.append(board.fen())
        clock_by_ply.append(extract_clock_comment(next_node.comment))
        max_fullmove_number = max(max_fullmove_number, board.fullmove_number)
        node = next_node

    return ParsedGame(
        game_id=_game_id_from_site(site),
        site=site,
        event=_optional_header(headers, "Event"),
        utc_date=_optional_header(headers, "UTCDate"),
        white=_optional_header(headers, "White"),
        black=_optional_header(headers, "Black"),
        white_elo=_required_int_header(headers, "WhiteElo"),
        black_elo=_required_int_header(headers, "BlackElo"),
        result=result,
        time_control=time_control,
        initial_time_sec=initial_time_sec,
        increment_sec=increment_sec,
        moves_san=moves_san,
        fens_after_move=fens_after_move,
        clock_by_ply=clock_by_ply,
        final_fullmove_number=max_fullmove_number,
        termination=_optional_header(headers, "Termination"),
    )


def _required_header(headers: chess.pgn.Headers, name: str) -> str:
    value = headers.get(name)
    if value is None or value == "" or value == "?":
        raise ValueError(f"Missing required PGN header {name!r}.")
    return value


def _optional_header(headers: chess.pgn.Headers, name: str) -> str | None:
    value = headers.get(name)
    if value is None or value == "" or value == "?":
        return None
    return value


def _required_int_header(headers: chess.pgn.Headers, name: str) -> int:
    value = _required_header(headers, name)
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"Invalid integer PGN header {name!r}: {value!r}.") from exc


def _game_id_from_site(site: str) -> str:
    game_id = site.rstrip("/").rsplit("/", maxsplit=1)[-1].strip()
    if not game_id:
        raise ValueError(f"Could not determine game id from Site header {site!r}.")
    return game_id
