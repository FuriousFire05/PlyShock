import json
from pathlib import Path

import pandas as pd
from plyshock.evaluation.ablation import (
    evaluate_majority_baseline,
    get_ablation_feature_sets,
    run_ablation_study,
)

MODEL_INPUT_FEATURES = [
    "rating_gap",
    "lower_is_white",
    "snapshot_move",
    "initial_time_sec",
    "increment_sec",
    "lower_clock_sec",
    "higher_clock_sec",
    "clock_diff_lower_minus_higher",
    "lower_clock_ratio",
    "higher_clock_ratio",
    "lower_time_pressure_flag",
    "higher_time_pressure_flag",
    "eval_cp_lower_pov",
    "eval_abs",
    "lower_is_better_by_engine",
    "mate_flag",
]


def test_get_ablation_feature_sets_returns_expected_keys() -> None:
    feature_sets = get_ablation_feature_sets(MODEL_INPUT_FEATURES)

    assert set(feature_sets) == {
        "rating_only",
        "rating_clock",
        "rating_engine",
        "rating_clock_engine",
        "full_plyshock",
    }
    assert feature_sets["rating_only"] == ["rating_gap", "lower_is_white"]
    assert feature_sets["full_plyshock"] == MODEL_INPUT_FEATURES


def test_get_ablation_feature_sets_ignores_missing_optional_features() -> None:
    feature_sets = get_ablation_feature_sets(["rating_gap"])

    assert feature_sets["rating_only"] == ["rating_gap"]
    assert feature_sets["rating_clock"] == ["rating_gap"]
    assert feature_sets["rating_engine"] == ["rating_gap"]


def test_evaluate_majority_baseline_returns_valid_metrics() -> None:
    metrics = evaluate_majority_baseline(
        train_y=pd.Series([1, 1, 1, 0]),
        test_y=pd.Series([1, 0, 1, 0]),
    )

    assert set(metrics) == {"accuracy", "precision", "recall", "f1", "roc_auc"}
    assert metrics["accuracy"] == 0.5
    assert metrics["roc_auc"] is None


def test_run_ablation_study_writes_json_and_plot_without_group_leakage(tmp_path: Path) -> None:
    output_json = tmp_path / "ablation.json"
    output_plot = tmp_path / "ablation.png"

    summary = run_ablation_study(
        _feature_dataframe(),
        {"model_input_features": MODEL_INPUT_FEATURES, "target_column": "upset_label"},
        output_metrics_path=output_json,
        output_plot_path=output_plot,
        test_size=0.25,
        random_state=7,
    )

    assert output_json.exists()
    assert output_plot.exists()
    assert summary["total_rows"] == 40
    assert summary["train_games"] + summary["test_games"] == 40
    assert set(summary["results"]) == {
        "majority_baseline",
        "rating_only",
        "rating_clock",
        "rating_engine",
        "rating_clock_engine",
        "full_plyshock",
    }
    assert summary["results"]["majority_baseline"]["roc_auc"] is None
    assert json.loads(output_json.read_text(encoding="utf-8")) == summary


def _feature_dataframe() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for index in range(40):
        label = index % 2
        rows.append(
            {
                "game_id": f"game-{index}",
                "rating_gap": 100 + index,
                "lower_is_white": index % 3 == 0,
                "snapshot_move": 15 + (index % 5) * 5,
                "initial_time_sec": 300,
                "increment_sec": 0,
                "lower_clock_sec": 30 + index,
                "higher_clock_sec": 45 + index,
                "clock_diff_lower_minus_higher": -15,
                "lower_clock_ratio": (30 + index) / 300,
                "higher_clock_ratio": (45 + index) / 300,
                "lower_time_pressure_flag": int(index < 5),
                "higher_time_pressure_flag": int(index < 3),
                "eval_cp_lower_pov": (index - 20) * 10,
                "eval_abs": abs((index - 20) * 10),
                "lower_is_better_by_engine": int(index > 20),
                "mate_flag": 0,
                "upset_label": label,
            }
        )
    return pd.DataFrame(rows)
