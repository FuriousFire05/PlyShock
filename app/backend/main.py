"""Minimal FastAPI backend for serving the trained PlyShock model."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException

from app.backend.model_loader import (
    build_feature_vector,
    get_model_input_features,
    load_feature_schema,
    load_json,
    load_model,
)
from app.backend.schemas import PredictRequest, PredictResponse

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = PROJECT_ROOT / "research" / "artifacts" / "models" / "best_model.joblib"
SCHEMA_PATH = PROJECT_ROOT / "research" / "data" / "processed" / "feature_schema_50k.json"
METRICS_PATH = PROJECT_ROOT / "research" / "artifacts" / "metrics" / "model_comparison.json"
ABLATION_PATH = PROJECT_ROOT / "research" / "artifacts" / "metrics" / "ablation_results_50k.json"
PREDICTIONS_PATH = PROJECT_ROOT / "research" / "artifacts" / "metrics" / "test_predictions.csv"

app = FastAPI(title="PlyShock Demo Backend")


@app.get("/health")
def health() -> dict[str, str | bool]:
    """Return basic service and artifact availability."""
    model_exists = MODEL_PATH.exists()
    schema_exists = SCHEMA_PATH.exists()

    return {
        "status": "ok" if model_exists and schema_exists else "degraded",
        "app": app.title,
        "model_exists": model_exists,
        "schema_exists": schema_exists,
    }


@app.get("/metrics")
def metrics() -> dict[str, Any]:
    """Return model comparison metrics, plus ablation metrics when available."""
    if not METRICS_PATH.exists():
        raise HTTPException(status_code=404, detail="Model comparison metrics file not found.")

    response: dict[str, Any] = {
        "model_comparison": load_json(METRICS_PATH),
    }
    if ABLATION_PATH.exists():
        response["ablation"] = load_json(ABLATION_PATH)
    return response


@app.get("/feature-schema")
def feature_schema() -> dict[str, Any]:
    """Return the feature schema JSON."""
    if not SCHEMA_PATH.exists():
        raise HTTPException(status_code=404, detail="Feature schema file not found.")
    return load_feature_schema(SCHEMA_PATH)


@app.get("/sample-predictions")
def sample_predictions() -> list[dict[str, Any]]:
    """Return the first 10 rows of saved test predictions, if available."""
    if not PREDICTIONS_PATH.exists():
        return []

    predictions = pd.read_csv(PREDICTIONS_PATH).head(10)
    predictions = predictions.where(pd.notna(predictions), None)
    return predictions.to_dict(orient="records")


@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest) -> PredictResponse:
    """Predict whether the lower-rated player wins from model features."""
    if not MODEL_PATH.exists():
        raise HTTPException(status_code=503, detail="Model artifact not found.")
    if not SCHEMA_PATH.exists():
        raise HTTPException(status_code=503, detail="Feature schema file not found.")

    try:
        model = load_model(MODEL_PATH)
        schema = load_feature_schema(SCHEMA_PATH)
        model_input_features = get_model_input_features(schema)
        feature_vector = build_feature_vector(request.features, model_input_features)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    prediction = model.predict(feature_vector)
    predicted_label = int(prediction[0])

    upset_probability: float | None = None
    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(feature_vector)[0]
        classes = getattr(model, "classes_", None)
        if classes is not None and 1 in classes:
            class_index = list(classes).index(1)
        else:
            class_index = 1 if len(probabilities) > 1 else 0
        upset_probability = float(probabilities[class_index])

    interpretation = (
        "Model predicts an upset."
        if predicted_label == 1
        else "Model predicts a non-upset."
    )

    return PredictResponse(
        upset_probability=upset_probability,
        predicted_label=predicted_label,
        interpretation=interpretation,
    )
