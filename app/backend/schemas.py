"""Pydantic schemas for the PlyShock demo backend."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

DEFAULT_SNAPSHOT_MOVES = [15, 20, 25, 30, 35]


class PredictRequest(BaseModel):
    features: dict[str, float | int | bool]


class PredictResponse(BaseModel):
    upset_probability: float | None
    predicted_label: int
    interpretation: str


class AnalyzePgnRequest(BaseModel):
    pgn_text: str
    depth: int = 8
    snapshot_moves: list[int] = Field(default_factory=lambda: DEFAULT_SNAPSHOT_MOVES.copy())


class AnalyzePgnReplayRequest(BaseModel):
    pgn_text: str
    eval_depth: int = 6
    prediction_depth: int = 8
    checkpoint_moves: list[int] = Field(default_factory=lambda: DEFAULT_SNAPSHOT_MOVES.copy())
    max_plies: int = 90


class LiveCheckpointHistoryItem(BaseModel):
    checkpoint_move: int
    eval_cp_lower_pov: float


class LiveEvaluateRequest(BaseModel):
    fen: str
    white_elo: int
    black_elo: int
    white_clock_sec: int | float | None
    black_clock_sec: int | float | None
    initial_time_sec: int | float
    increment_sec: int | float
    fullmove_number: int
    ply: int
    checkpoint_history: list[LiveCheckpointHistoryItem] = Field(default_factory=list)
    eval_depth: int = 6
    prediction_depth: int = 8


class DemoGameInfo(BaseModel):
    id: str
    filename: str
    path: str
    label: str | None = None
    white_elo: int | None = None
    black_elo: int | None = None
    result: str | None = None
    rating_gap: int | None = None
    lower_rated_color: str | None = None
    actual_upset_label: int | None = None


class AnalysisResponse(BaseModel):
    metadata: dict[str, Any]
    snapshots: list[dict[str, Any]]
    summary: dict[str, Any]


class ReplayResponse(BaseModel):
    metadata: dict[str, Any]
    moves: list[dict[str, Any]]
    checkpoints: list[dict[str, Any]]
    summary: dict[str, Any]


class LiveEvaluateResponse(BaseModel):
    stockfish_eval_cp_white_pov: int
    stockfish_bar: float
    lower_rated_color: str
    higher_rated_color: str
    rating_gap: int
    lower_clock_sec: int | float | None
    higher_clock_sec: int | float | None
    is_checkpoint: bool
    checkpoint_move: int | None
    plyshock: dict[str, Any] | None
