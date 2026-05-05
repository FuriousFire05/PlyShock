"""Utilities for loading PlyShock demo backend artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import pandas as pd


def load_json(path: str | Path) -> Any:
    """Load a JSON file from disk."""
    with Path(path).open("r", encoding="utf-8") as file:
        return json.load(file)


def load_model(path: str | Path) -> Any:
    """Load a persisted model artifact."""
    return joblib.load(path)


def load_feature_schema(path: str | Path) -> dict[str, Any]:
    """Load the feature schema JSON."""
    schema = load_json(path)
    if not isinstance(schema, dict):
        raise ValueError("Feature schema must be a JSON object.")
    return schema


def get_model_input_features(schema: dict[str, Any]) -> list[str]:
    """Return model input feature names from a schema."""
    features = schema.get("model_input_features")
    if not isinstance(features, list) or not all(isinstance(item, str) for item in features):
        raise ValueError("Feature schema must include a 'model_input_features' list of strings.")
    return features


def build_feature_vector(
    input_features: dict[str, float | int | bool],
    model_input_features: list[str],
) -> pd.DataFrame:
    """Build a one-row feature dataframe in the exact order expected by the model."""
    missing_features = [
        feature for feature in model_input_features if feature not in input_features
    ]
    if missing_features:
        missing = ", ".join(missing_features)
        raise ValueError(f"Missing required model feature(s): {missing}")

    ordered_features = {
        feature: input_features[feature] for feature in model_input_features
    }
    return pd.DataFrame([ordered_features], columns=model_input_features)
