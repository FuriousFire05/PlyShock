"""Minimal FastAPI backend for serving the trained PlyShock model."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from app.backend.model_loader import (
    build_feature_vector,
    get_model_input_features,
    load_feature_schema,
    load_json,
    load_model,
)
from app.backend.pgn_demo import (
    DemoAnalysisError,
    analyze_pgn_replay_text,
    analyze_pgn_text,
    summarize_pgn_text,
)
from app.backend.schemas import (
    AnalysisResponse,
    AnalyzePgnReplayRequest,
    AnalyzePgnRequest,
    DemoGameInfo,
    PredictRequest,
    PredictResponse,
    ReplayResponse,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = PROJECT_ROOT / "research" / "artifacts" / "models" / "best_model.joblib"
SCHEMA_PATH = PROJECT_ROOT / "research" / "data" / "processed" / "feature_schema_50k.json"
METRICS_PATH = PROJECT_ROOT / "research" / "artifacts" / "metrics" / "model_comparison.json"
ABLATION_PATH = PROJECT_ROOT / "research" / "artifacts" / "metrics" / "ablation_results_50k.json"
PREDICTIONS_PATH = PROJECT_ROOT / "research" / "artifacts" / "metrics" / "test_predictions.csv"
STOCKFISH_PATH = PROJECT_ROOT / "research" / "tools" / "stockfish" / "stockfish.exe"
DEMO_GAMES_DIR = Path(__file__).resolve().parent / "demo_games"

app = FastAPI(title="PlyShock Demo Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str | bool | int]:
    """Return basic service and artifact availability."""
    model_exists = MODEL_PATH.exists()
    schema_exists = SCHEMA_PATH.exists()
    stockfish_exists = STOCKFISH_PATH.exists()

    return {
        "status": "ok" if model_exists and schema_exists and stockfish_exists else "degraded",
        "app": app.title,
        "model_exists": model_exists,
        "schema_exists": schema_exists,
        "stockfish_exists": stockfish_exists,
        "demo_games_count": len(_list_demo_game_paths()),
        "replay_supported": True,
        "upload_pgn_supported": True,
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


@app.get("/demo-games", response_model=list[DemoGameInfo])
def demo_games() -> list[DemoGameInfo]:
    """Return bundled demo PGN files."""
    return [_demo_game_info(path) for path in _list_demo_game_paths()]


@app.get("/demo-games/{game_id}", response_class=PlainTextResponse)
def demo_game(game_id: str) -> str:
    """Return raw PGN text for one bundled demo game."""
    path = _get_demo_game_path(game_id)
    return path.read_text(encoding="utf-8")


@app.get("/demo-games/{game_id}/analysis", response_model=AnalysisResponse)
def demo_game_analysis(
    game_id: str,
    depth: int = 8,
    snapshot_moves: Annotated[list[int] | None, Query()] = None,
) -> AnalysisResponse:
    """Analyze a bundled demo PGN and return a mid-game prediction timeline."""
    path = _get_demo_game_path(game_id)
    request = AnalyzePgnRequest(
        pgn_text=path.read_text(encoding="utf-8"),
        depth=depth,
        snapshot_moves=snapshot_moves or [15, 20, 25, 30, 35],
    )
    return _run_pgn_analysis(request)


@app.get("/demo-games/{game_id}/replay", response_model=ReplayResponse)
def demo_game_replay(
    game_id: str,
    eval_depth: int = 6,
    prediction_depth: int = 8,
    checkpoint_moves: Annotated[list[int] | None, Query()] = None,
    max_plies: int = 90,
) -> ReplayResponse:
    """Analyze a bundled demo PGN and return full replay data."""
    path = _get_demo_game_path(game_id)
    request = AnalyzePgnReplayRequest(
        pgn_text=path.read_text(encoding="utf-8"),
        eval_depth=eval_depth,
        prediction_depth=prediction_depth,
        checkpoint_moves=checkpoint_moves or [15, 20, 25, 30, 35],
        max_plies=max_plies,
    )
    return _run_pgn_replay_analysis(request)


@app.post("/analyze-pgn", response_model=AnalysisResponse)
def analyze_pgn(request: AnalyzePgnRequest) -> AnalysisResponse:
    """Analyze a submitted PGN and return a mid-game prediction timeline."""
    return _run_pgn_analysis(request)


@app.post("/analyze-pgn-replay", response_model=ReplayResponse)
def analyze_pgn_replay(request: AnalyzePgnReplayRequest) -> ReplayResponse:
    """Analyze a submitted PGN and return full replay data."""
    return _run_pgn_replay_analysis(request)


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


def _run_pgn_analysis(request: AnalyzePgnRequest) -> AnalysisResponse:
    try:
        result = analyze_pgn_text(
            pgn_text=request.pgn_text,
            depth=request.depth,
            snapshot_moves=request.snapshot_moves,
            model_path=MODEL_PATH,
            schema_path=SCHEMA_PATH,
            stockfish_path=STOCKFISH_PATH,
        )
    except DemoAnalysisError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error

    return AnalysisResponse(**result)


def _run_pgn_replay_analysis(request: AnalyzePgnReplayRequest) -> ReplayResponse:
    try:
        result = analyze_pgn_replay_text(
            pgn_text=request.pgn_text,
            eval_depth=request.eval_depth,
            prediction_depth=request.prediction_depth,
            checkpoint_moves=request.checkpoint_moves,
            max_plies=request.max_plies,
            model_path=MODEL_PATH,
            schema_path=SCHEMA_PATH,
            stockfish_path=STOCKFISH_PATH,
        )
    except DemoAnalysisError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error

    return ReplayResponse(**result)


def _list_demo_game_paths() -> list[Path]:
    if not DEMO_GAMES_DIR.exists():
        return []
    return sorted(path for path in DEMO_GAMES_DIR.glob("*.pgn") if path.is_file())


def _demo_game_info(path: Path) -> DemoGameInfo:
    summary: dict[str, object] = {}
    try:
        summary = summarize_pgn_text(path.read_text(encoding="utf-8"))
    except Exception:
        summary = {"label": path.stem.replace("_", " ").title()}

    return DemoGameInfo(
        id=path.stem,
        filename=path.name,
        path=path.relative_to(PROJECT_ROOT).as_posix(),
        label=_optional_str(summary.get("label")),
        white_elo=_optional_int(summary.get("white_elo")),
        black_elo=_optional_int(summary.get("black_elo")),
        result=_optional_str(summary.get("result")),
        rating_gap=_optional_int(summary.get("rating_gap")),
        lower_rated_color=_optional_str(summary.get("lower_rated_color")),
        actual_upset_label=_optional_int(summary.get("actual_upset_label")),
    )


def _get_demo_game_path(game_id: str) -> Path:
    for path in _list_demo_game_paths():
        if game_id in {path.stem, path.name}:
            return path
    raise HTTPException(status_code=404, detail=f"Demo game {game_id!r} not found.")


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)
