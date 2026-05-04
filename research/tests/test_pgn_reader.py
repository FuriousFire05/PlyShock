from pathlib import Path

from plyshock.parsing.pgn_reader import parse_single_game, read_pgn_games

SAMPLE_PGN = Path("research/data/samples/sample.pgn")


def test_read_pgn_games_parses_sample() -> None:
    games = read_pgn_games(SAMPLE_PGN)

    assert games


def test_read_pgn_games_sample_metadata() -> None:
    game = read_pgn_games(SAMPLE_PGN, max_games=1)[0]

    assert game.game_id
    assert isinstance(game.white_elo, int)
    assert isinstance(game.black_elo, int)
    assert game.result in {"1-0", "0-1", "1/2-1/2"}
    assert game.initial_time_sec == 300
    assert game.increment_sec == 0


def test_read_pgn_games_sample_move_lengths_match() -> None:
    game = read_pgn_games(SAMPLE_PGN, max_games=1)[0]

    assert len(game.moves_san) == len(game.fens_after_move)
    assert len(game.moves_san) == len(game.clock_by_ply)


def test_read_pgn_games_sample_has_clock_values() -> None:
    game = read_pgn_games(SAMPLE_PGN, max_games=1)[0]

    assert any(clock is not None for clock in game.clock_by_ply)


def test_read_pgn_games_honors_max_games_zero() -> None:
    assert read_pgn_games(SAMPLE_PGN, max_games=0) == []


def test_read_pgn_games_skips_invalid_games(tmp_path: Path) -> None:
    malformed_pgn = tmp_path / "malformed.pgn"
    malformed_pgn.write_text(
        """[Site "https://lichess.org/badgame"]
[Result "1-0"]
[WhiteElo "not-a-number"]
[BlackElo "2000"]
[TimeControl "300+0"]

1. e4 1-0

""",
        encoding="utf-8",
    )

    assert read_pgn_games(malformed_pgn) == []


def test_parse_single_game_extracts_mainline_data() -> None:
    games = read_pgn_games(SAMPLE_PGN, max_games=1)
    game = games[0]

    assert game.game_id == "PpwPOZMq"
    assert game.moves_san[:4] == ["e4", "c5", "Nf3", "Nc6"]
    assert game.clock_by_ply[:2] == [30, 30]
    assert game.final_fullmove_number >= 13


def test_parse_single_game_is_imported_for_public_api_smoke() -> None:
    assert parse_single_game is not None
