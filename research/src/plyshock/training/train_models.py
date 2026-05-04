"""Train and compare classical models for PlyShock."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from plyshock.training.model_registry import build_model_registry
from plyshock.training.split import create_group_train_test_split

LEAKAGE_COLUMNS = {
    "result",
    "winner_color",
    "final_fullmove_number",
    "fen",
    "game_id",
    "time_control",
}


def train_and_evaluate_models(
    df: pd.DataFrame,
    feature_schema: dict[str, Any],
    output_dir: str | Path,
    metrics_dir: str | Path,
    plots_dir: str | Path,
    test_size: float = 0.2,
    random_state: int = 42,
) -> dict[str, object]:
    """Train all registered models and save metrics, artifacts, and plots.

    Args:
        df: Final feature dataframe.
        feature_schema: Schema containing ``model_input_features`` and ``target_column``.
        output_dir: Directory for trained model artifacts.
        metrics_dir: Directory for metrics CSV/JSON files.
        plots_dir: Directory for plots.
        test_size: Fraction of game groups assigned to test.
        random_state: Random seed for split and model registry.

    Returns:
        Model comparison summary dictionary.
    """
    model_features = list(feature_schema["model_input_features"])
    target_column = str(feature_schema["target_column"])
    _validate_feature_schema(df, model_features, target_column)

    models_path = Path(output_dir)
    metrics_path = Path(metrics_dir)
    plot_path = Path(plots_dir)
    models_path.mkdir(parents=True, exist_ok=True)
    metrics_path.mkdir(parents=True, exist_ok=True)
    plot_path.mkdir(parents=True, exist_ok=True)

    train_df, test_df = create_group_train_test_split(
        df, group_col="game_id", test_size=test_size, random_state=random_state
    )
    x_train = _model_matrix(train_df, model_features)
    y_train = train_df[target_column].astype(int)
    x_test = _model_matrix(test_df, model_features)
    y_test = test_df[target_column].astype(int)

    models = build_model_registry(random_state=random_state)
    metrics_by_model: dict[str, dict[str, float | None]] = {}
    predictions = pd.DataFrame(
        {
            "game_id": test_df["game_id"].to_list(),
            "y_true": y_test.to_list(),
        },
        index=test_df.index,
    )

    best_model_name: str | None = None
    best_f1 = -1.0
    trained_models: dict[str, object] = {}
    for model_name, model in models.items():
        model.fit(x_train, y_train)
        trained_models[model_name] = model
        joblib.dump(model, models_path / f"{model_name}.joblib")

        y_pred = model.predict(x_test)
        y_score = _prediction_scores(model, x_test)
        metrics = _compute_metrics(y_test, y_pred, y_score)
        metrics_by_model[model_name] = metrics
        predictions[f"{model_name}_prediction"] = y_pred
        if y_score is not None:
            predictions[f"{model_name}_score"] = y_score

        model_f1 = metrics["f1"] or 0.0
        if model_f1 > best_f1:
            best_f1 = model_f1
            best_model_name = model_name

    if best_model_name is None:
        raise ValueError("No models were trained.")

    joblib.dump(trained_models[best_model_name], models_path / "best_model.joblib")
    predictions.to_csv(metrics_path / "test_predictions.csv", index=False)
    _write_model_comparison_csv(metrics_by_model, metrics_path / "model_comparison.csv")

    random_forest = trained_models["random_forest"]
    random_forest_pred = predictions["random_forest_prediction"].astype(int)
    _plot_confusion_matrix(
        y_test, random_forest_pred, plot_path / "confusion_matrix_random_forest.png"
    )
    _plot_feature_importance(
        random_forest,
        model_features,
        plot_path / "feature_importance_random_forest.png",
    )

    summary: dict[str, object] = {
        "total_rows": int(len(df)),
        "train_rows": int(len(train_df)),
        "test_rows": int(len(test_df)),
        "train_games": int(train_df["game_id"].nunique()),
        "test_games": int(test_df["game_id"].nunique()),
        "feature_count": len(model_features),
        "target_column": target_column,
        "best_model": best_model_name,
        "models": metrics_by_model,
    }
    (metrics_path / "model_comparison.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    return summary


def _validate_feature_schema(
    df: pd.DataFrame, model_features: list[str], target_column: str
) -> None:
    leakage_features = LEAKAGE_COLUMNS.intersection(model_features)
    if leakage_features:
        leaked = ", ".join(sorted(leakage_features))
        raise ValueError(f"Feature schema includes leakage columns: {leaked}.")

    required_columns = set(model_features) | {target_column, "game_id"}
    missing_columns = required_columns.difference(df.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Training dataframe is missing required columns: {missing}.")


def _model_matrix(df: pd.DataFrame, model_features: list[str]) -> pd.DataFrame:
    return df.loc[:, model_features].apply(pd.to_numeric, errors="coerce").fillna(0)


def _prediction_scores(model: object, x_test: pd.DataFrame) -> list[float] | None:
    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(x_test)
        return probabilities[:, 1].tolist()
    if hasattr(model, "decision_function"):
        scores = model.decision_function(x_test)
        return pd.Series(scores).astype(float).to_list()
    return None


def _compute_metrics(
    y_true: pd.Series, y_pred: pd.Series | list[int], y_score: list[float] | None
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


def _write_model_comparison_csv(
    metrics_by_model: dict[str, dict[str, float | None]], path: Path
) -> None:
    rows = [{"model": model_name, **metrics} for model_name, metrics in metrics_by_model.items()]
    pd.DataFrame(rows).to_csv(path, index=False)


def _plot_confusion_matrix(y_true: pd.Series, y_pred: pd.Series, path: Path) -> None:
    matrix = confusion_matrix(y_true, y_pred, labels=[0, 1])
    figure, axis = plt.subplots()
    axis.imshow(matrix)
    axis.set_title("Random Forest Confusion Matrix")
    axis.set_xlabel("Predicted")
    axis.set_ylabel("Actual")
    axis.set_xticks([0, 1], labels=["0", "1"])
    axis.set_yticks([0, 1], labels=["0", "1"])
    for row_index in range(matrix.shape[0]):
        for column_index in range(matrix.shape[1]):
            axis.text(column_index, row_index, str(matrix[row_index, column_index]), ha="center")
    figure.tight_layout()
    figure.savefig(path)
    plt.close(figure)


def _plot_feature_importance(model: object, feature_names: list[str], path: Path) -> None:
    importances = getattr(model, "feature_importances_", None)
    if importances is None:
        return

    importance_frame = pd.DataFrame(
        {"feature": feature_names, "importance": importances}
    ).sort_values("importance", ascending=False)
    figure, axis = plt.subplots(figsize=(10, 6))
    axis.bar(importance_frame["feature"], importance_frame["importance"])
    axis.set_title("Random Forest Feature Importance")
    axis.set_xlabel("Feature")
    axis.set_ylabel("Importance")
    figure.autofmt_xdate(rotation=90)
    figure.tight_layout()
    figure.savefig(path)
    plt.close(figure)
