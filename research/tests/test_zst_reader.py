from pathlib import Path

import zstandard as zstd
from plyshock.parsing.zst_reader import read_pgn_games_streaming

SAMPLE_PGN = Path("research/data/samples/sample.pgn")


def test_read_pgn_games_streaming_reads_plain_sample() -> None:
    games = read_pgn_games_streaming(SAMPLE_PGN)

    assert games


def test_read_pgn_games_streaming_reads_zst_sample(tmp_path: Path) -> None:
    compressed_sample = _compressed_sample(tmp_path)

    games = read_pgn_games_streaming(compressed_sample)

    assert games


def test_read_pgn_games_streaming_max_games_one_for_plain_sample() -> None:
    games = read_pgn_games_streaming(SAMPLE_PGN, max_games=1)

    assert len(games) == 1


def test_read_pgn_games_streaming_max_games_one_for_zst_sample(tmp_path: Path) -> None:
    compressed_sample = _compressed_sample(tmp_path)

    games = read_pgn_games_streaming(compressed_sample, max_games=1)

    assert len(games) == 1


def _compressed_sample(tmp_path: Path) -> Path:
    compressed_sample = tmp_path / "sample.pgn.zst"
    compressor = zstd.ZstdCompressor()
    with SAMPLE_PGN.open("rb") as source, compressed_sample.open("wb") as target:
        compressor.copy_stream(source, target)
    return compressed_sample
