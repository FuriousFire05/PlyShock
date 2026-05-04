import json
from pathlib import Path

import pandas as pd
from plyshock.parsing.pgn_reader import read_pgn_games
from plyshock.pipelines.build_filtered_games import build_filtered_games, parsed_game_to_record

SAMPLE_PGN = Path("research/data/samples/sample.pgn")


def test_parsed_game_to_record_includes_expected_label_fields() -> None:
    game = read_pgn_games(SAMPLE_PGN, max_games=1)[0]

    record = parsed_game_to_record(game)

    assert record["game_id"] == "PpwPOZMq"
    assert record["winner_color"] == "black"
    assert record["rating_gap"] == 100
    assert record["higher_rated_color"] == "white"
    assert record["lower_rated_color"] == "black"
    assert record["lower_is_white"] is False
    assert record["upset_label"] == 1


def test_build_filtered_games_writes_parquet_and_summary(tmp_path: Path) -> None:
    output_path = tmp_path / "filtered_games.parquet"
    summary_path = tmp_path / "summary.json"

    summary = build_filtered_games(
        input_path=SAMPLE_PGN,
        output_path=output_path,
        summary_path=summary_path,
        max_games=1,
        min_fullmove=13,
    )

    assert output_path.exists()
    assert summary_path.exists()
    assert summary["parsed_games"] == 1
    assert summary["accepted_games"] == 1
    assert summary["rejection_reasons"] == {}
    assert summary["upset_count"] == 1
    assert summary["non_upset_count"] == 0

    saved_summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert saved_summary == summary


def test_build_filtered_games_output_parquet_can_be_read(tmp_path: Path) -> None:
    output_path = tmp_path / "filtered_games.parquet"
    summary_path = tmp_path / "summary.json"

    build_filtered_games(
        input_path=SAMPLE_PGN,
        output_path=output_path,
        summary_path=summary_path,
        max_games=1,
        min_fullmove=13,
    )

    dataframe = pd.read_parquet(output_path)

    assert len(dataframe) == 1
    assert dataframe.loc[0, "game_id"] == "PpwPOZMq"
    assert dataframe.loc[0, "upset_label"] == 1


def test_build_filtered_games_respects_max_games_one(tmp_path: Path) -> None:
    output_path = tmp_path / "filtered_games.parquet"
    summary_path = tmp_path / "summary.json"

    summary = build_filtered_games(
        input_path=SAMPLE_PGN,
        output_path=output_path,
        summary_path=summary_path,
        max_games=1,
        min_fullmove=13,
    )

    assert summary["parsed_games"] == 1


def test_build_filtered_games_empty_accepted_dataset_does_not_crash(tmp_path: Path) -> None:
    output_path = tmp_path / "filtered_games.parquet"
    summary_path = tmp_path / "summary.json"

    summary = build_filtered_games(
        input_path=SAMPLE_PGN,
        output_path=output_path,
        summary_path=summary_path,
        max_games=1,
        min_fullmove=999,
    )

    dataframe = pd.read_parquet(output_path)

    assert output_path.exists()
    assert summary_path.exists()
    assert dataframe.empty
    assert "game_id" in dataframe.columns
    assert summary["parsed_games"] == 1
    assert summary["accepted_games"] == 0
    assert summary["rejected_games"] == 1
    assert summary["rejection_reasons"] == {"game_too_short": 1}
