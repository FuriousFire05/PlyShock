from pathlib import Path

import pandas as pd
import pytest
from plyshock.evaluation.plots import plot_confusion_matrix_from_csv
from plyshock.pipelines.plot_model_results import main


def test_plot_confusion_matrix_from_csv_writes_svm_plot(tmp_path: Path) -> None:
    predictions_path = tmp_path / "test_predictions.csv"
    output_path = tmp_path / "confusion_matrix_svm.png"
    _write_predictions(predictions_path)

    plot_confusion_matrix_from_csv(predictions_path, "svm", output_path)

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_plot_confusion_matrix_from_csv_raises_helpful_error_for_missing_column(
    tmp_path: Path,
) -> None:
    predictions_path = tmp_path / "test_predictions.csv"
    pd.DataFrame({"y_true": [0, 1], "random_forest_prediction": [0, 1]}).to_csv(
        predictions_path, index=False
    )

    with pytest.raises(ValueError, match="svm_prediction"):
        plot_confusion_matrix_from_csv(predictions_path, "svm", tmp_path / "plot.png")


def test_plot_model_results_cli_writes_output(tmp_path: Path) -> None:
    predictions_path = tmp_path / "test_predictions.csv"
    output_path = tmp_path / "confusion_matrix_svm.png"
    _write_predictions(predictions_path)

    main(["--predictions", str(predictions_path), "--model", "svm", "--output", str(output_path)])

    assert output_path.exists()


def _write_predictions(path: Path) -> None:
    pd.DataFrame(
        {
            "game_id": ["a", "b", "c", "d"],
            "y_true": [0, 1, 1, 0],
            "svm_prediction": [0, 1, 0, 0],
            "svm_score": [0.1, 0.8, 0.4, 0.2],
        }
    ).to_csv(path, index=False)
