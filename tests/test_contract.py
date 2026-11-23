"""The shipped artifact must satisfy the JSON contract the integration expects."""

import json
from pathlib import Path

import pytest

from nuri_mvp.areas import AREAS
from nuri_mvp.pipeline import SCHEMA_VERSION, Predictor

MODEL_DIR = Path(__file__).resolve().parents[1] / "models"

LONG_TEXT = (
    "아이가 공원에서 나뭇잎을 주워 색깔별로 늘어놓고 왜 색이 다른지 계속 물어봤습니다.\n"
    "집에 와서는 그 나뭇잎으로 그림을 만들었고, 테이프로 붙이는 방법을 스스로 찾았습니다.\n"
    "동생이 나뭇잎을 가져가자 싫다고 말하고 다시 달라고 이야기했습니다."
)


@pytest.fixture(scope="module")
def predictor() -> Predictor:
    return Predictor.from_dir(MODEL_DIR)


def test_payload_shape(predictor: Predictor) -> None:
    payload = predictor.predict(LONG_TEXT)
    assert payload["schema_version"] == SCHEMA_VERSION
    assert payload["strongest_area"] in AREAS
    assert payload["second_area"] in AREAS
    assert payload["weakest_area"] in AREAS
    assert payload["strongest_area"] != payload["second_area"]
    assert len(payload["areas"]) == len(AREAS)
    assert {entry["area"] for entry in payload["areas"]} == set(AREAS)


def test_ranking_is_sorted_and_normalized(predictor: Predictor) -> None:
    payload = predictor.predict(LONG_TEXT)
    probabilities = [entry["probability"] for entry in payload["areas"]]
    assert probabilities == sorted(probabilities, reverse=True)
    assert [entry["rank"] for entry in payload["areas"]] == [1, 2, 3, 4, 5]
    assert abs(sum(probabilities) - 1.0) < 1e-4
    assert payload["strongest_area"] == payload["areas"][0]["area"]
    assert payload["weakest_area"] == payload["areas"][-1]["area"]


def test_confidence_matches_probabilities(predictor: Predictor) -> None:
    payload = predictor.predict(LONG_TEXT)
    confidence = payload["confidence"]
    assert confidence["top1_probability"] == payload["areas"][0]["probability"]
    assert confidence["gap_top1_top2"] == pytest.approx(
        payload["areas"][0]["probability"] - payload["areas"][1]["probability"], abs=1e-6
    )


def test_segment_counts_are_reported(predictor: Predictor) -> None:
    payload = predictor.predict(LONG_TEXT)
    assert payload["segments"]["used"] == 3
    assert payload["segments"]["aggregation"] == "mean_area_probability"
    assert payload["segments"]["chars"] == len(LONG_TEXT.strip())


def test_prediction_is_deterministic(predictor: Predictor) -> None:
    assert predictor.predict(LONG_TEXT) == predictor.predict(LONG_TEXT)


def test_payload_is_json_serializable(predictor: Predictor) -> None:
    payload = predictor.predict(LONG_TEXT)
    assert json.loads(json.dumps(payload, ensure_ascii=False)) == payload


def test_model_metadata_is_attached(predictor: Predictor) -> None:
    payload = predictor.predict(LONG_TEXT)
    assert payload["model"]["name"]
    assert payload["model"]["trained_at"]
    assert payload["model"]["data_sha256"]["train.csv"]


@pytest.mark.parametrize("text", ["", "   ", "\n"])
def test_empty_input_is_rejected(predictor: Predictor, text: str) -> None:
    with pytest.raises(ValueError, match="empty"):
        predictor.predict(text)
