import json
from pathlib import Path

from plyshock.pipelines.write_results_summary import write_results_summary


def test_write_results_summary_writes_markdown_and_identifies_best_models(
    tmp_path: Path,
) -> None:
    models_json = tmp_path / "model_comparison.json"
    eda_json = tmp_path / "eda_summary.json"
    feature_json = tmp_path / "feature_summary.json"
    output_path = tmp_path / "results_summary.md"
    models_json.write_text(json.dumps(_model_summary()), encoding="utf-8")
    eda_json.write_text(json.dumps(_eda_summary()), encoding="utf-8")
    feature_json.write_text(json.dumps(_feature_summary()), encoding="utf-8")

    content = write_results_summary(models_json, eda_json, output_path, feature_json)

    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8") == content
    assert "## Filtered Game Dataset / EDA Summary" in content
    assert "## Snapshot Model Dataset Summary" in content
    assert "## Model Comparison Table" in content
    assert "- Filtered game upset count: 34" in content
    assert "- Snapshot upset row count: 120" in content
    assert "- Snapshot non-upset row count: 260" in content
    assert "- Snapshot rows dropped for missing eval: 20" in content
    assert "  - 15: 100" in content
    assert "Best model by F1: random_forest (0.812)." in content
    assert "Best model by ROC-AUC: svm (0.901)." in content
    assert "Best model by accuracy: random_forest (0.778)." in content
    assert "| decision_tree | 0.712 | 0.623 | 0.500 | 0.555 | 0.650 |" in content
    assert "- Filtered game upset rate: 0.345" in content
    assert "suggest" in content


def _model_summary() -> dict[str, object]:
    return {
        "total_rows": 100,
        "train_rows": 80,
        "test_rows": 20,
        "train_games": 50,
        "test_games": 12,
        "feature_count": 26,
        "target_column": "upset_label",
        "best_model": "random_forest",
        "models": {
            "decision_tree": {
                "accuracy": 0.7119,
                "precision": 0.6234,
                "recall": 0.5,
                "f1": 0.5554,
                "roc_auc": 0.65,
            },
            "random_forest": {
                "accuracy": 0.7782,
                "precision": 0.8,
                "recall": 0.825,
                "f1": 0.8124,
                "roc_auc": 0.8751,
            },
            "svm": {
                "accuracy": 0.734,
                "precision": 0.75,
                "recall": 0.7,
                "f1": 0.724,
                "roc_auc": 0.9012,
            },
        },
    }


def _eda_summary() -> dict[str, object]:
    return {
        "total_games": 100,
        "upset_count": 34,
        "non_upset_count": 66,
        "upset_rate": 0.3454,
        "rating_gap_min": 100,
        "rating_gap_max": 650,
        "rating_gap_mean": 187.3456,
        "upset_rate_by_rating_gap_bucket": {
            "100-199": 0.33333,
            "200-399": 0.41234,
        },
    }


def _feature_summary() -> dict[str, object]:
    return {
        "total_input_rows": 400,
        "total_output_rows": 380,
        "dropped_missing_eval_rows": 20,
        "upset_count": 120,
        "non_upset_count": 260,
        "snapshot_counts_by_move": {
            "15": 100,
            "20": 90,
        },
    }
