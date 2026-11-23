"""Area model: loading data, fitting, saving and evaluating.

The estimator is the validated configuration from the experiment repository:

* features: character 2-5 gram TF-IDF over NFC/lowercased/collapsed text
* classifier: LinearSVC (C=10) wrapped in sigmoid calibration
* calibration folds: group-aware 5-fold over training ``group_id`` values,
  so an indicator group never calibrates on itself
"""

from __future__ import annotations

import csv
import hashlib
import json
import platform
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, cast

import joblib
import numpy as np
import sklearn
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, f1_score, top_k_accuracy_score
from sklearn.model_selection import GroupKFold
from sklearn.svm import LinearSVC

from nuri_mvp.areas import AREAS
from nuri_mvp.text import normalize_syllables

if TYPE_CHECKING:
    from collections.abc import Sequence

    import numpy.typing as npt
    from scipy.sparse import csr_matrix

SEED: Final[int] = 42
AREA_C: Final[float] = 10.0
FOLDS: Final[int] = 5
NGRAM_RANGE: Final[tuple[int, int]] = (2, 5)
MODEL_FILE: Final[str] = "area_model.joblib"
METADATA_FILE: Final[str] = "metadata.json"
MODEL_NAME: Final[str] = "char_2-5_tfidf+linear_svc_c10_calibrated"
REQUIRED_COLUMNS: Final[frozenset[str]] = frozenset({"id", "text", "label", "group_id", "source"})


class DataError(ValueError):
    """Raised when the shipped CSV files are missing columns or leak between splits."""


@dataclass(frozen=True, slots=True)
class Row:
    """One labeled observation record; only ``text`` is used as a feature."""

    identifier: str
    text: str
    label: str
    group: str
    source: str


def read_rows(path: Path) -> tuple[Row, ...]:
    """Read one split CSV and validate its schema and labels."""
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or ())
        if missing:
            message = f"{path.name}: missing columns {sorted(missing)}"
            raise DataError(message)
        rows: list[Row] = []
        for record in reader:
            text = record["text"] or ""
            if record["label"] not in AREAS:
                message = f"{path.name} line {reader.line_num}: unknown label {record['label']!r}"
                raise DataError(message)
            if not normalize_syllables(text) or not record["group_id"]:
                message = f"{path.name} line {reader.line_num}: empty text or group_id"
                raise DataError(message)
            rows.append(
                Row(
                    identifier=record["id"],
                    text=text,
                    label=record["label"],
                    group=record["group_id"],
                    source=record["source"],
                )
            )
    if not rows:
        message = f"{path.name}: empty dataset"
        raise DataError(message)
    return tuple(rows)


def load_splits(data_dir: Path) -> tuple[tuple[Row, ...], tuple[Row, ...]]:
    """Load ``train.csv`` and ``val.csv`` and reject group/text leakage."""
    train = read_rows(data_dir / "train.csv")
    val = read_rows(data_dir / "val.csv")
    if {row.group for row in train} & {row.group for row in val}:
        message = "train/val share a group_id; the split is not group-disjoint"
        raise DataError(message)
    if {normalize_syllables(row.text) for row in train} & {
        normalize_syllables(row.text) for row in val
    }:
        message = "train/val share an identical normalized text"
        raise DataError(message)
    if {row.label for row in train} != set(AREAS) or {row.label for row in val} != set(AREAS):
        message = "both splits must contain all five areas"
        raise DataError(message)
    return train, val


def build_vectorizer() -> TfidfVectorizer:
    """Return the train-only TF-IDF configuration used by the validated model."""
    return TfidfVectorizer(
        analyzer="char",
        preprocessor=normalize_syllables,
        lowercase=False,
        ngram_range=NGRAM_RANGE,
        sublinear_tf=True,
        min_df=1,
        norm="l2",
        dtype=np.float64,
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@dataclass(frozen=True, slots=True)
class AreaModel:
    """A fitted vectorizer plus calibrated classifier with training metadata."""

    vectorizer: TfidfVectorizer
    classifier: CalibratedClassifierCV
    metadata: dict[str, Any]

    @property
    def areas(self) -> tuple[str, ...]:
        """Class order of the classifier, which fixes probability column order."""
        return tuple(str(label) for label in self.classifier.classes_)

    def predict_proba(self, texts: Sequence[str]) -> npt.NDArray[np.float64]:
        """Return one probability row per text, columns ordered by :attr:`areas`."""
        matrix = cast("csr_matrix", self.vectorizer.transform(list(texts)))
        proba: npt.NDArray[np.float64] = self.classifier.predict_proba(matrix)
        return proba

    def save(self, model_dir: Path) -> Path:
        """Persist the estimator and its metadata; returns the estimator path."""
        model_dir.mkdir(parents=True, exist_ok=True)
        path = model_dir / MODEL_FILE
        _ = joblib.dump(
            {"vectorizer": self.vectorizer, "classifier": self.classifier},
            path,
            compress=3,
        )
        _ = (model_dir / METADATA_FILE).write_text(
            json.dumps(self.metadata, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path

    @classmethod
    def load(cls, model_dir: Path) -> AreaModel:
        """Load a saved estimator; raises ``FileNotFoundError`` when untrained."""
        path = model_dir / MODEL_FILE
        meta_path = model_dir / METADATA_FILE
        if not path.exists() or not meta_path.exists():
            message = f"no trained model in {model_dir}; run the train command first"
            raise FileNotFoundError(message)
        bundle = cast("dict[str, Any]", joblib.load(path))
        metadata = cast("dict[str, Any]", json.loads(meta_path.read_text(encoding="utf-8")))
        return cls(
            vectorizer=cast("TfidfVectorizer", bundle["vectorizer"]),
            classifier=cast("CalibratedClassifierCV", bundle["classifier"]),
            metadata=metadata,
        )


def fit_areas(rows: Sequence[Row], *, data_dir: Path) -> AreaModel:
    """Fit the calibrated area model on ``rows`` using group-aware calibration folds."""
    texts = [row.text for row in rows]
    labels = [row.label for row in rows]
    groups = np.array([row.group for row in rows])
    vectorizer = build_vectorizer()
    matrix = cast("csr_matrix", vectorizer.fit_transform(texts))
    splits = list(GroupKFold(n_splits=FOLDS).split(matrix, labels, groups))
    classifier = CalibratedClassifierCV(
        LinearSVC(C=AREA_C, dual=True, max_iter=10000, random_state=SEED),
        cv=splits,
        method="sigmoid",
    ).fit(matrix, labels)
    metadata: dict[str, Any] = {
        "schema_version": "1.0",
        "model_name": MODEL_NAME,
        "trained_at": datetime.now(tz=UTC).isoformat(timespec="seconds"),
        "python": platform.python_version(),
        "scikit_learn": sklearn.__version__,
        "seed": SEED,
        "params": {
            "features": "char 2-5 gram TF-IDF, sublinear_tf, min_df=1, l2, train-only fit",
            "preprocessor": "NFC, lowercase Latin, whitespace collapse",
            "classifier": f"LinearSVC C={AREA_C:g}, sigmoid calibration",
            "calibration_cv": f"GroupKFold({FOLDS}) over group_id",
        },
        "data": {
            "train_rows": len(rows),
            "train_groups": len({row.group for row in rows}),
            "label_counts": {area: labels.count(area) for area in AREAS},
            "sha256": {name: _sha256(data_dir / name) for name in ("train.csv", "val.csv")},
        },
        "areas": list(AREAS),
    }
    return AreaModel(vectorizer=vectorizer, classifier=classifier, metadata=metadata)


def area_scores(truth: Sequence[str], predicted: Sequence[str]) -> dict[str, Any]:
    """Per-area precision and recall against the gold labels."""
    scores: dict[str, Any] = {}
    for area in AREAS:
        true_positive = sum(
            1 for gold, pred in zip(truth, predicted, strict=True) if gold == pred == area
        )
        gold_n = sum(1 for gold in truth if gold == area)
        pred_n = sum(1 for pred in predicted if pred == area)
        scores[area] = {
            "gold_n": gold_n,
            "predicted_n": pred_n,
            "recall": true_positive / gold_n if gold_n else 0.0,
            "precision": true_positive / pred_n if pred_n else 0.0,
        }
    return scores


def evaluate(model: AreaModel, rows: Sequence[Row]) -> dict[str, Any]:
    """Compute accuracy, Macro-F1, top-2 and per-area scores on the given rows."""
    texts = [row.text for row in rows]
    truth = [row.label for row in rows]
    proba = model.predict_proba(texts)
    areas = np.array(model.areas)
    predicted = [str(area) for area in areas[np.argmax(proba, axis=1)]]
    return {
        "n_rows": len(rows),
        "n_groups": len({row.group for row in rows}),
        "accuracy": float(accuracy_score(truth, predicted)),
        "macro_f1": float(f1_score(truth, predicted, average="macro", zero_division=0)),
        "top2_accuracy": float(
            top_k_accuracy_score(truth, proba, k=2, labels=list(areas))  # type: ignore[arg-type]
        ),
        "per_area": area_scores(truth, predicted),
        "note": (
            "Exploratory validation score on the shipped split; the split was also used "
            "during model selection in the experiment repository."
        ),
    }
