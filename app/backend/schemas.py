"""Pydantic schemas for the PlyShock demo backend."""

from __future__ import annotations

from pydantic import BaseModel


class PredictRequest(BaseModel):
    features: dict[str, float | int | bool]


class PredictResponse(BaseModel):
    upset_probability: float | None
    predicted_label: int
    interpretation: str
