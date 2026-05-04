"""Ablation study utilities for PlyShock feature sets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score

from plyshock.training.split import create_group_train_test_split

METRIC_NAMES = ["accuracy", "precision", "recall", "f1", "roc_auc"]
RATING_ONLY_FEATURES = ["rating_gap", "lower_is_white"]
RATING_CLOCK_FEATURES = [
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
]
RATING_ENGINE_FEATURES = [
    "rating_gap",
    "lower_is_white",
    "snapshot_move",
    "eval_cp_lower_pov",
    "eval_abs",
    "lower_is_better_by_engine",
    "mate_flag",
]


def get_ablation_feature_sets(model_input_features: list[str]) -> dict[str, list[str]]:
    """Return schema-safe ablation feature sets.

    Args:
        model_input_features: Feature names available for model input.

    Returns:
        Mapping of ablation name to feature list, with unavailable optional features removed.
    """
    available_features = set(model_input_features)
    rating_clock_engine = _dedupe(RATING_CLOCK_FEATURES + RATING_ENGINE_FEATURES)
    feature_sets = {
        "rating_only": RATING_ONLY_FEATURES,
        "rating_clock": RATING_CLOCK_FEATURES,
        "rating_engine": RATING_ENGINE_FEATURES,
        "rating_clock_engine": rating_clock_engine,
        "full_plyshock": model_input_features,
    }
    return {
        name: [feature for feature in features if feature in available_features]
        for name, features in feature_sets.items()
    }


def evaluate_majority_baseline(
    train_y: pd.Series | list[int], test_y: pd.Series | list[int]
) -> dict[str, float | None]:
    """Evaluate a majority-class predictor fitted on the training target."""
    train_series = pd.Series(train_y).astype(int)
    test_series = pd.Series(test_y).astype(int)
    majority_class = int(train_series.mode().sort_values().iloc[0])
    predictions = pd.Series([majority_class] * len(test_series), index=test_series.index)
    return _compute_metrics(test_series, predictions, y_score=None)


def run_ablation_study(
    df: pd.DataFrame,
    feature_schema: dict[str, object],
    output_metrics_path: str | Path,
    output_plot_path: str | Path,
    test_size: float = 0.2,
    random_state: int = 42,
) -> dict[str, object]:
    """Run majority and feature-subset ablations using a group-safe split.

    Args:
        df: Feature dataframe.
        feature_schema: Schema with ``model_input_features`` and ``target_column``.
        output_metrics_path: Destination JSON path.
        output_plot_path: Destination F1 bar plot path.
        test_size: Fraction of game groups assigned to test.
        random_state: Random seed.

    Returns:
        Summary dictionary written to ``output_metrics_path``.
    """
    model_input_features = list(feature_schema["model_input_features"])
    target_column = str(feature_schema["target_column"])
    train_df, test_df = create_group_train_test_split(
        df, group_col="game_id", test_size=test_size, random_state=random_state
    )
    train_y = train_df[target_column].astype(int)
    test_y = test_df[target_column].astype(int)
    feature_sets = get_ablation_feature_sets(model_input_features)

    results: dict[str, dict[str, float | None]] = {
        "majority_baseline": evaluate_majority_baseline(train_y, test_y)
    }
    for ablation_name, features in feature_sets.items():
        if not features:
            results[ablation_name] = {metric: None for metric in METRIC_NAMES}
            continue

        model = RandomForestClassifier(
            n_estimators=200,
            class_weight="balanced",
            random_state=random_state,
            n_jobs=-1,
        )
        train_x = _model_matrix(train_df, features)
        test_x = _model_matrix(test_df, features)
        model.fit(train_x, train_y)
        predictions = model.predict(test_x)
        probabilities = model.predict_proba(test_x)[:, 1]
        results[ablation_name] = _compute_metrics(test_y, predictions, probabilities)

    summary: dict[str, object] = {
        "total_rows": int(len(df)),
        "train_rows": int(len(train_df)),
        "test_rows": int(len(test_df)),
        "train_games": int(train_df["game_id"].nunique()),
        "test_games": int(test_df["game_id"].nunique()),
        "target_column": target_column,
        "feature_sets": feature_sets,
        "results": results,
    }
    metrics_path = Path(output_metrics_path)
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    _write_f1_plot(results, Path(output_plot_path))
    return summary


def _compute_metrics(
    y_true: pd.Series, y_pred: pd.Series | list[int], y_score: Any | None
) -> dict[str, float | None]:
    metrics: dict[str, float | None] = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, average="binary", zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, average="binary", zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, average="binary", zero_division=0)),
        "roc_auc": None,
    }
    if y_score is not None and y_true.nunique() == 2:
        metrics["roc_auc"] = float(roc_auc_score(y_true, y_score))
    return metrics


def _model_matrix(df: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    return df.loc[:, features].apply(pd.to_numeric, errors="coerce").fillna(0)


def _write_f1_plot(results: dict[str, dict[str, float | None]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    labels = list(results)
    f1_values = [float(results[label]["f1"] or 0.0) for label in labels]
    figure, axis = plt.subplots(figsize=(10, 5))
    axis.bar(labels, f1_values)
    axis.set_title("PlyShock Ablation F1 Comparison")
    axis.set_xlabel("Ablation")
    axis.set_ylabel("F1 score")
    figure.autofmt_xdate(rotation=45)
    figure.tight_layout()
    figure.savefig(output_path)
    plt.close(figure)


def _dedupe(features: list[str]) -> list[str]:
    return list(dict.fromkeys(features))
