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


class DemoGameInfo(BaseModel):
    id: str
    filename: str
    path: str


class AnalysisResponse(BaseModel):
    metadata: dict[str, Any]
    snapshots: list[dict[str, Any]]
    summary: dict[str, Any]


class ReplayResponse(BaseModel):
    metadata: dict[str, Any]
    moves: list[dict[str, Any]]
    checkpoints: list[dict[str, Any]]
    summary: dict[str, Any]
