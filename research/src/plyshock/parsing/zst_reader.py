"""Streaming readers for plain and zstd-compressed Lichess PGN files."""

from __future__ import annotations

import io
from pathlib import Path
from typing import BinaryIO, TextIO

import chess.pgn
import zstandard as zstd

from plyshock.parsing.pgn_reader import ParsedGame, parse_single_game


def open_text_stream(path: str | Path) -> TextIO:
    """Open a plain text or zstd-compressed PGN file as a UTF-8 text stream.

    Args:
        path: Path to a ``.pgn`` or ``.pgn.zst`` file.

    Returns:
        A text stream. For ``.zst`` files, bytes are decompressed incrementally.
    """
    file_path = Path(path)
    if file_path.name.endswith(".zst"):
        compressed_file = file_path.open("rb")
        stream_reader = zstd.ZstdDecompressor().stream_reader(compressed_file)
        return _ZstdTextStream(stream_reader, compressed_file, encoding="utf-8")

    return file_path.open(encoding="utf-8")


def read_pgn_games_streaming(path: str | Path, max_games: int | None = None) -> list[ParsedGame]:
    """Read valid PGN games from a plain or zstd-compressed file.

    Args:
        path: Path to a ``.pgn`` or ``.pgn.zst`` file.
        max_games: Maximum number of valid games to return. ``None`` reads all games.

    Returns:
        Parsed games. Invalid games are skipped consistently with ``read_pgn_games``.

    Raises:
        ValueError: If ``max_games`` is negative.
    """
    if max_games is not None and max_games < 0:
        raise ValueError("max_games must be non-negative or None.")

    parsed_games: list[ParsedGame] = []
    with open_text_stream(path) as pgn_stream:
        while max_games is None or len(parsed_games) < max_games:
            game = chess.pgn.read_game(pgn_stream)
            if game is None:
                break

            if game.errors:
                continue

            try:
                parsed_games.append(parse_single_game(game))
            except ValueError:
                continue

    return parsed_games


class _ZstdTextStream(io.TextIOWrapper):
    """Text wrapper that also closes the compressed source file."""

    def __init__(self, buffer: BinaryIO, compressed_file: BinaryIO, *, encoding: str) -> None:
        super().__init__(buffer, encoding=encoding)
        self._compressed_file = compressed_file

    def close(self) -> None:
        try:
            super().close()
        finally:
            self._compressed_file.close()
