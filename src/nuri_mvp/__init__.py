"""Nuri area MVP: long Korean text to strongest and second strongest area."""

from __future__ import annotations

from nuri_mvp.model import AreaModel, Row, evaluate, fit_areas, load_splits
from nuri_mvp.pipeline import SCHEMA_VERSION, Predictor

__all__ = [
    "SCHEMA_VERSION",
    "AreaModel",
    "Predictor",
    "Row",
    "evaluate",
    "fit_areas",
    "load_splits",
]
