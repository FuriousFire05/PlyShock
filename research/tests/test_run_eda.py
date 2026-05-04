import json
from pathlib import Path

import pandas as pd
import pytest
from plyshock.pipelines.run_eda import PLOT_FILENAMES, run_eda


def test_run_eda_writes_metrics_and_plots(tmp_path: Path) -> None:
    input_path = _write_tiny_dataset(tmp_path)
    metrics_path = tmp_path / "reports" / "eda_metrics.json"
    plots_dir = tmp_path / "plots"

    metrics = run_eda(input_path, metrics_path, plots_dir)

    assert metrics_path.exists()
    assert set(PLOT_FILENAMES) == {path.name for path in plots_dir.iterdir()}
    assert metrics["total_games"] == 4
    assert metrics["upset_rate"] == 0.5

    saved_metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert saved_metrics == metrics
    for plot_filename in PLOT_FILENAMES:
        assert (plots_dir / plot_filename).is_file()


def test_run_eda_empty_dataframe_raises_value_error(tmp_path: Path) -> None:
    input_path = tmp_path / "empty.parquet"
    pd.DataFrame(
        columns=["game_id", "rating_gap", "upset_label", "final_fullmove_number"]
    ).to_parquet(input_path, index=False)

    with pytest.raises(ValueError, match="empty"):
        run_eda(input_path, tmp_path / "metrics.json", tmp_path / "plots")


def _write_tiny_dataset(tmp_path: Path) -> Path:
    input_path = tmp_path / "filtered_games.parquet"
    dataframe = pd.DataFrame(
        {
            "game_id": ["game-1", "game-2", "game-3", "game-4"],
            "rating_gap": [100, 150, 275, 450],
            "upset_label": [1, 0, 1, 0],
            "final_fullmove_number": [20, 35, 42, 55],
        }
    )
    dataframe.to_parquet(input_path, index=False)
    return input_path
