import json
from pathlib import Path

import pandas as pd
import pytest
from plyshock.training.train_models import train_and_evaluate_models

FEATURES = [
    "rating_gap",
    "snapshot_move",
    "eval_cp_lower_pov",
    "lower_clock_ratio",
]


def test_train_and_evaluate_models_writes_metrics_and_artifacts(tmp_path: Path) -> None:
    models_dir = tmp_path / "models"
    metrics_dir = tmp_path / "metrics"
    plots_dir = tmp_path / "plots"
    dataframe = _training_dataframe()
    schema = {"model_input_features": FEATURES, "target_column": "upset_label"}

    summary = train_and_evaluate_models(
        dataframe,
        schema,
        output_dir=models_dir,
        metrics_dir=metrics_dir,
        plots_dir=plots_dir,
        test_size=0.25,
        random_state=7,
    )

    assert (metrics_dir / "model_comparison.json").exists()
    assert (metrics_dir / "model_comparison.csv").exists()
    assert (metrics_dir / "test_predictions.csv").exists()
    assert (models_dir / "best_model.joblib").exists()
    assert (plots_dir / "confusion_matrix_random_forest.png").exists()
    assert (plots_dir / "feature_importance_random_forest.png").exists()
    assert summary["feature_count"] == len(FEATURES)
    assert summary["target_column"] == "upset_label"
    assert summary["best_model"] in {
        "decision_tree",
        "knn",
        "naive_bayes",
        "svm",
        "random_forest",
    }
    assert set(summary["models"]) == {
        "decision_tree",
        "knn",
        "naive_bayes",
        "svm",
        "random_forest",
    }

    saved_summary = json.loads((metrics_dir / "model_comparison.json").read_text())
    comparison = pd.read_csv(metrics_dir / "model_comparison.csv")
    assert saved_summary["best_model"] == summary["best_model"]
    assert set(comparison["model"]) == set(summary["models"])


def test_train_and_evaluate_models_rejects_leakage_features(tmp_path: Path) -> None:
    dataframe = _training_dataframe()
    schema = {
        "model_input_features": FEATURES + ["game_id"],
        "target_column": "upset_label",
    }

    with pytest.raises(ValueError, match="leakage"):
        train_and_evaluate_models(
            dataframe,
            schema,
            output_dir=tmp_path / "models",
            metrics_dir=tmp_path / "metrics",
            plots_dir=tmp_path / "plots",
            test_size=0.25,
            random_state=7,
        )


def _training_dataframe() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for index in range(40):
        label = index % 2
        rows.append(
            {
                "game_id": f"game-{index}",
                "rating_gap": 100 + index,
                "snapshot_move": 15 + (index % 5) * 5,
                "eval_cp_lower_pov": (index - 20) * 10,
                "lower_clock_ratio": 0.1 + index / 100,
                "result": "0-1",
                "winner_color": "black",
                "final_fullmove_number": 35,
                "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
                "time_control": "300+0",
                "upset_label": label,
            }
        )
    return pd.DataFrame(rows)
