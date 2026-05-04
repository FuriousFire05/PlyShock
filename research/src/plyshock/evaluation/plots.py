"""Plotting helpers for model evaluation artifacts."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import confusion_matrix


def plot_confusion_matrix_for_model(
    predictions: pd.DataFrame,
    model_name: str,
    output_path: str | Path,
) -> None:
    """Plot a confusion matrix for a selected model's predictions.

    Args:
        predictions: Dataframe containing ``y_true`` and ``{model_name}_prediction``.
        model_name: Model name prefix used in the predictions CSV.
        output_path: Destination PNG path.

    Raises:
        ValueError: If required columns are missing.
    """
    prediction_column = f"{model_name}_prediction"
    _validate_prediction_columns(predictions, prediction_column)

    y_true = predictions["y_true"].astype(int)
    y_pred = predictions[prediction_column].astype(int)
    matrix = confusion_matrix(y_true, y_pred, labels=[0, 1])

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots()
    axis.imshow(matrix)
    axis.set_title(f"Confusion Matrix: {model_name}")
    axis.set_xlabel("Predicted")
    axis.set_ylabel("Actual")
    axis.set_xticks([0, 1], labels=["0", "1"])
    axis.set_yticks([0, 1], labels=["0", "1"])
    for row_index in range(matrix.shape[0]):
        for column_index in range(matrix.shape[1]):
            axis.text(column_index, row_index, str(matrix[row_index, column_index]), ha="center")
    figure.tight_layout()
    figure.savefig(destination)
    plt.close(figure)


def plot_confusion_matrix_from_csv(
    predictions_path: str | Path,
    model_name: str,
    output_path: str | Path,
) -> None:
    """Read a predictions CSV and plot a selected model confusion matrix."""
    predictions = pd.read_csv(predictions_path)
    plot_confusion_matrix_for_model(predictions, model_name, output_path)


def _validate_prediction_columns(predictions: pd.DataFrame, prediction_column: str) -> None:
    missing_columns = [
        column for column in ["y_true", prediction_column] if column not in predictions.columns
    ]
    if missing_columns:
        available = ", ".join(predictions.columns)
        missing = ", ".join(missing_columns)
        raise ValueError(
            f"Prediction CSV is missing required column(s): {missing}. "
            f"Available columns: {available}."
        )
