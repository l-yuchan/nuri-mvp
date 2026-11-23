"""Training, evaluation and split-integrity checks on the shipped CSVs."""

import csv
import shutil
from pathlib import Path

import pytest

from nuri_mvp.model import (
    AreaModel,
    DataError,
    evaluate,
    fit_areas,
    load_splits,
)

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "data"
MODEL_DIR = REPO / "models"


def test_shipped_split_is_group_disjoint() -> None:
    train, val = load_splits(DATA)
    assert len(train) == 666
    assert len(val) == 158
    assert not {row.group for row in train} & {row.group for row in val}


def test_training_reproduces_reported_accuracy(tmp_path: Path) -> None:
    train, val = load_splits(DATA)
    model = fit_areas(train, data_dir=DATA)
    metrics = evaluate(model, val)
    # Documented validation score is 0.7152 / 0.8924 on this split.
    assert metrics["accuracy"] == pytest.approx(0.7152, abs=0.01)
    assert metrics["macro_f1"] == pytest.approx(0.7087, abs=0.01)
    assert metrics["top2_accuracy"] == pytest.approx(0.8924, abs=0.01)
    assert set(metrics["per_area"]) == set(model.areas)


def test_saved_artifact_round_trips(tmp_path: Path) -> None:
    train, _ = load_splits(DATA)
    model = fit_areas(train, data_dir=DATA)
    path = model.save(tmp_path)
    assert path.exists()
    loaded = AreaModel.load(tmp_path)
    assert loaded.areas == model.areas
    texts = [train[0].text, train[1].text]
    assert loaded.predict_proba(texts).shape == (2, len(model.areas))


def test_group_leak_is_rejected(tmp_path: Path) -> None:
    for name in ("train.csv", "val.csv"):
        shutil.copyfile(DATA / name, tmp_path / name)
    with (DATA / "train.csv").open(encoding="utf-8-sig", newline="") as handle:
        train_row = next(csv.DictReader(handle))
    with (tmp_path / "val.csv").open("a", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "X999",
                train_row["source"],
                train_row["session"],
                train_row["group_id"],
                train_row["label"],
                "",
                "",
                "",
                "",
                "",
                "",
                train_row["text"],
                "",
                "",
                "",
                "",
                "",
            ]
        )
    with pytest.raises(DataError, match="group"):
        load_splits(tmp_path)


def test_missing_artifact_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        AreaModel.load(tmp_path)
