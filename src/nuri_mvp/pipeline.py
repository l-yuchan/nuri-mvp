"""Long text to a ranked area result.

The public contract is :meth:`Predictor.predict`: a description string in, a
JSON-serializable dict out. Sentence-level probabilities are averaged with equal
weight; that aggregation matched the strongest observed evidence, where pooling
two or three observations improved within-child ranking over using one.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Final

from nuri_mvp.model import MODEL_FILE, AreaModel
from nuri_mvp.text import split_observations

if TYPE_CHECKING:
    from collections.abc import Sequence

SCHEMA_VERSION: Final[str] = "1.0"
DEFAULT_MODEL_DIR: Final[Path] = Path("models")

__all__ = ["DEFAULT_MODEL_DIR", "MODEL_FILE", "SCHEMA_VERSION", "Predictor"]


class Predictor:
    """Wire a fitted :class:`AreaModel` to the text-to-result contract."""

    def __init__(self, model: AreaModel) -> None:
        """Wrap an already loaded model."""
        self._model = model

    @classmethod
    def from_dir(cls, model_dir: Path | str = DEFAULT_MODEL_DIR) -> Predictor:
        """Load the shipped artifact from a model directory."""
        return cls(AreaModel.load(Path(model_dir)))

    @property
    def areas(self) -> tuple[str, ...]:
        """Area names in the model's probability column order."""
        return self._model.areas

    def predict(self, text: str) -> dict[str, Any]:
        """Score one description and return the ranked-area payload.

        Raises:
            ValueError: if the description is empty or whitespace only.

        """
        if not text.strip():
            message = "input text is empty"
            raise ValueError(message)
        segments = split_observations(text)
        if not segments:
            message = "input text has no scorable segment"
            raise ValueError(message)

        areas = self.areas
        mean_proba = self._model.predict_proba(segments).mean(axis=0)
        probabilities = [float(value) for value in mean_proba]
        order = sorted(range(len(areas)), key=lambda index: (-probabilities[index], index))

        ranked: list[dict[str, Any]] = []
        for position, index in enumerate(order):
            ranked.append(
                {
                    "rank": position + 1,
                    "area": areas[index],
                    "probability": round(probabilities[index], 6),
                }
            )
        top1_probability = float(ranked[0]["probability"])
        top2_probability = float(ranked[1]["probability"])
        metadata: dict[str, Any] = self._model.metadata
        data: dict[str, Any] = metadata.get("data") or {}
        return {
            "schema_version": SCHEMA_VERSION,
            "strongest_area": areas[order[0]],
            "second_area": areas[order[1]],
            "weakest_area": areas[order[-1]],
            "areas": ranked,
            "confidence": {
                "top1_probability": round(top1_probability, 6),
                "gap_top1_top2": round(top1_probability - top2_probability, 6),
            },
            "segments": {
                "used": len(segments),
                "chars": len(text.strip()),
                "aggregation": "mean_area_probability",
            },
            "model": {
                "name": metadata.get("model_name"),
                "trained_at": metadata.get("trained_at"),
                "data_sha256": data.get("sha256"),
            },
        }

    def predict_batch(self, texts: Sequence[str]) -> list[dict[str, Any]]:
        """Score several descriptions independently."""
        return [self.predict(text) for text in texts]
