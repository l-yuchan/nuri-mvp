# Prediction contract (schema 1.0)

The integration system calls one function and reads one JSON object. Nothing else
from this repository is required at runtime except the `models/` directory.

## Entry points

| Form | Call | Notes |
|---|---|---|
| Python | `Predictor.from_dir("models").predict(text)` | preferred; load once at startup |
| Python | `Predictor(model).predict_batch([...])` | loops `predict`, one result per input |
| CLI | `python -m nuri_mvp predict --text ...` or `--file path` | prints the same JSON on stdout |

`predict` is pure: same text in, same payload out. It does not keep session state,
so calling it repeatedly for the same child is the integration's responsibility to
combine (or simply concatenate descriptions before calling).

## Input

- One string, UTF-8, any length. Lines and sentence-final punctuation (`.!?…。？！`)
  are the segmentation boundaries.
- Segments shorter than 8 characters are dropped (interjections, speaker labels).
- If nothing survives (no punctuation, very short text), the whole stripped text is
  scored as one segment.
- Empty or whitespace-only input raises `ValueError`; the CLI prints
  `{"error": "input text is empty"}` and exits with code 2.

## Output

| Field | Type | Meaning |
|---|---|---|
| `schema_version` | string | `"1.0"`; bump on any breaking change |
| `strongest_area` | string | area with the highest mean probability |
| `second_area` | string | second highest; never equal to `strongest_area` |
| `weakest_area` | string | last place in the ranking. **Experimental**: not validated as a judgment, do not present as an assessment |
| `areas` | array of 5 objects | `{rank, area, probability}`, sorted by probability desc, probabilities sum to 1 (rounded to 6 dp) |
| `confidence.top1_probability` | float | probability of `strongest_area` |
| `confidence.gap_top1_top2` | float | `top1 - top2`; small gap means the top two are close |
| `segments.used` | int | number of sentence segments that were scored |
| `segments.chars` | int | stripped input length |
| `segments.aggregation` | string | always `"mean_area_probability"` |
| `model.name` | string | model id |
| `model.trained_at` | string | ISO-8601 UTC timestamp of the shipped artifact |
| `model.data_sha256` | object | hashes of the training CSVs the artifact was fit on |

Area names are exactly: `사회관계`, `신체운동·건강`, `예술경험`, `의사소통`, `자연탐구`.

## Semantics the integration must respect

1. `strongest_area` is the model's best single area for the description. At the
   validation level this matches the gold area 71.5% of the time.
2. `second_area` is the next candidate. The **ordering of the top two has not been
   validated**: top-2 accuracy only says the gold area was one of them.
   Phrase it as "가장 두드러지는 영역 + 다음 후보", not as "1등 영역, 2등 영역".
3. Probabilities are calibrated per segment and then averaged over segments, so they
   are comparable within one response, not across responses or across children.
4. `weakest_area` is informational only. Do not show it as a developmental judgment.
5. There is no abstention. Short or off-topic text still yields five probabilities.

## Latency and deployment

| Step | Measured |
|---|---|
| `Predictor.from_dir` (cold, imports pandas-free sklearn) | 186 ms |
| `predict` on 200-400 character descriptions | median 5.0 ms, p95 6.3 ms |
| Artifact size | 4.8 MB joblib |

Everything runs on CPU. The demo target is a laptop, so no device-specific path is
needed. One `Predictor` instance is enough; concurrent calls from multiple threads
were not tested.

## Compatibility

The artifact was written with scikit-learn 1.9.1 / joblib 1.6.0 (Python 3.14 in the
reference environment; `requires-python >= 3.11`). Pin scikit-learn to the same minor
series in the integration environment, or call the CLI in a subprocess if the
integration uses a different stack.

## Errors

| Condition | Python | CLI |
|---|---|---|
| empty text | `ValueError("input text is empty")` | exit 2, `{"error": ...}` |
| no scorable segment | `ValueError("input text has no scorable segment")` | exit 2 |
| model directory missing | `FileNotFoundError` | exit 2 |
| CSV leakage or schema problem at train time | `nuri_mvp.model.DataError` | exit 2 |
