# Nuri area MVP

Long Korean description of a child -> **strongest Nuri area** and **second strongest area**.

This repository is the ML deliverable for the integration system. It is deliberately
small: one classifier, one artifact, one JSON contract, no experiment code. The
research record (all tested alternatives, probes, item-level work) stays in the
`ml/` experiment directory and is summarized in [docs/findings.md](docs/findings.md).

```
description text
   -> split into sentence-level segments
   -> per-segment calibrated area probabilities (5 areas)
   -> mean over segments
   -> ranked areas, strongest / second / weakest
```

## Current performance

Validation split shipped with the data: 158 records over 13 indicator groups
(`data/val.csv`, `models/metrics.json`).

| Metric | Value |
|---|---:|
| Top-1 area accuracy | 0.7152 |
| Macro-F1 | 0.7087 |
| Top-2 accuracy (true area in ranks 1-2) | 0.8924 |

These are exploratory validation scores on the same split that was used for model
selection in the experiment repository; there is no separate test set yet. The
long-text path (segmentation + averaging) is not part of that number: it was checked
on three hand-written example descriptions only (see [examples/](examples/)).
Read [docs/model_card.md](docs/model_card.md) before quoting any number.

## Quickstart

Requires Python 3.11+.

```sh
uv venv
uv pip install -e ".[dev]"
uv run python -m nuri_mvp evaluate     # score the shipped artifact on data/val.csv
uv run pytest                          # 23 tests, including a retrain-to-0.7152 check
```

Without uv:

```sh
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"
.venv/Scripts/python -m nuri_mvp evaluate
```

Retraining is reproducible from `data/train.csv` and takes a few seconds:

```sh
uv run python -m nuri_mvp train        # rewrites models/area_model.joblib + metadata
```

## Use it

```python
from nuri_mvp import Predictor

predictor = Predictor.from_dir("models")  # once, at startup
result = predictor.predict("아이가 색종이를 오려 ...")  # any length of Korean text

result["strongest_area"]  # "예술경험"
result["second_area"]  # "사회관계"
result["areas"]  # all five, ranked, with probabilities
```

From the command line:

```sh
uv run python -m nuri_mvp predict --file examples/inputs/parent_01_art.txt
uv run python -m nuri_mvp predict --text "아이가 블록으로 높은 탑을 쌓았습니다."
```

Example response (`examples/outputs/parent_01_art.json`, shortened):

```json
{
  "schema_version": "1.0",
  "strongest_area": "예술경험",
  "second_area": "사회관계",
  "weakest_area": "신체운동·건강",
  "areas": [
    {"rank": 1, "area": "예술경험", "probability": 0.362781},
    {"rank": 2, "area": "사회관계", "probability": 0.291988},
    {"rank": 3, "area": "의사소통", "probability": 0.14291},
    {"rank": 4, "area": "자연탐구", "probability": 0.128783},
    {"rank": 5, "area": "신체운동·건강", "probability": 0.073539}
  ],
  "confidence": {"top1_probability": 0.362781, "gap_top1_top2": 0.070793},
  "segments": {"used": 4, "chars": 194, "aggregation": "mean_area_probability"},
  "model": {"name": "char_2-5_tfidf+linear_svc_c10_calibrated", "trained_at": "...", "data_sha256": {"...": "..."}}
}
```

The full field-by-field contract, error behaviour and integration options are in
[docs/interface.md](docs/interface.md).

Measured on this machine (CPU, Python 3.14 in the reference environment): model load
186 ms once, single prediction median 5.0 ms, p95 6.3 ms.

## What it does not do

- No item (indicator) level output, no developmental level 1-4, no recommendation,
  no LED mapping, no speech input. Those are outside this MVP.
- No "not enough evidence" abstention. Every non-empty input gets a ranking; the
  weakest area is a by-product of the ranking and is **not** validated as a judgment.
- Korean text only, and the shipped model has never been evaluated on spontaneously
  spoken or transcribed parent speech.

## Repository layout

```
data/           train.csv, val.csv (fixed split, see docs/data_sheet.md)
models/         shipped artifact (joblib, ~4.8 MB) + metadata.json + metrics.json
src/nuri_mvp/   areas.py, text.py, model.py, pipeline.py, cli.py
tests/          text, contract, and training-reproduction tests
examples/       three hand-written long descriptions + the JSON they produce
docs/           interface.md, model_card.md, data_sheet.md, findings.md
```

## Data note

The dataset contains KICCE observation scales and Ministry of Education casebook
excerpts provided for the course project. Do not publish the CSV files or the
derived model outside the team / course context. See [docs/data_sheet.md](docs/data_sheet.md).
