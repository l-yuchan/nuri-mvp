# Model card: Nuri area classifier v0.1.0

## Intended use

Given a Korean description of one child's behavior during an activity, return the
Nuri area that the description most strongly evidences, plus a second candidate.
Scope of this MVP: 5-area classification only.

Intended consumers: the team's integration system (voice transcript -> text ->
this model -> display), and demo/pitch material.

## Out of scope

- Item (indicator) level analysis, developmental level 1-4, strong/weak **items**.
- Cross-child comparison, developmental diagnosis, or any clinical claim.
- Speech recognition, dialogue management, recommendation, map/LED output.
- English or mixed-language input; the training data is Korean only.

## Training data

- `data/train.csv`: 666 records, 57 indicator groups, five areas.
  - KICCE observation scale vignettes (indicator + level 1-4, three vignettes per level).
  - Ministry of Education / Ministry of Health and Welfare casebook excerpts.
- `data/val.csv`: 158 records, 13 groups, used here for reporting only.
- Only the `text` column is a feature. `label` is the target. `item_text`,
  `content_category`, `group_id`, `session` are label- or source-derived and are
  never used as input.
- Provenance, licensing and known label ambiguities: [data_sheet.md](data_sheet.md).

## Model

| Element | Setting |
|---|---|
| Features | character 2-5 gram TF-IDF, sublinear TF, `min_df=1`, L2 normalized, fit on train only |
| Preprocessing | Unicode NFC, Latin lowercase, whitespace collapse; no morphological analyzer |
| Classifier | `LinearSVC(C=10)` + sigmoid calibration |
| Calibration CV | `GroupKFold(5)` over `group_id`, so an indicator group never calibrates on itself |
| Seed | 42 (deterministic given the same library versions) |
| Inference | segments the input by sentence, averages the five area probabilities |

Why this model: it is the best-scoring configuration in the experiment repository
(71.5% top-1 / 89.2% top-2). fastText (62.7%), frozen multilingual-E5 + linear SVM
(52.5%), and web-corpus initialization did not beat it on the same split. Details and
references: [findings.md](findings.md).

## Validation results

From `models/metrics.json` (158 records, 13 groups):

| Metric | Value |
|---|---:|
| Accuracy | 0.7152 |
| Macro-F1 | 0.7087 |
| Top-2 accuracy | 0.8924 |

Per area (gold n / predicted n / recall / precision):

| Area | gold n | predicted n | recall | precision |
|---|---:|---:|---:|---:|
| 자연탐구 | 40 | 45 | 0.825 | 0.733 |
| 신체운동·건강 | 27 | 25 | 0.778 | 0.840 |
| 예술경험 | 28 | 27 | 0.750 | 0.778 |
| 의사소통 | 34 | 40 | 0.735 | 0.625 |
| 사회관계 | 29 | 21 | 0.448 | 0.619 |

Interpretation limits:

1. The split was also used to select the configuration in the experiment repository,
   so this is an exploratory validation score, not an independent test estimate.
2. 158 records are only 13 independent groups; row-level accuracy overstates
   precision. Group-mean accuracy is 0.713 (worst group 0.167).
3. These numbers are for **single observation records**. The long-text path used by
   the integration is unvalidated beyond three hand-written examples.

## Known weaknesses

- **사회관계 under-selection.** Recall 0.448: the model predicts 사회관계 for 21 of 158
  records while 29 are gold. In a demo, 사회관계 rarely appears as the strongest area.
  Cause is documented in the probe study: for some indicator groups the scene's theme
  and the assessed area diverge (for example a family scene labeled 사회관계, leaf
  textures labeled 예술경험). Strong external judges also fail on those groups.
- **Group-level outliers.** One validation group (`KI-3-04`, family scene) is correct
  for only 17% of its rows.
- **No abstention.** Empty evidence still returns probabilities; the integration must
  not present a "weakest area" as an assessment.
- **Spoken/transcribed input** (ASR errors, fillers, multiple speakers) is untested.
- Calibration is per segment; averaging segments changes the effective confidence, so
  do not tune a threshold on the averaged probability without new labels.

## Ethical / privacy notes

Descriptions are about children. The model returns coarse area labels and is not a
developmental screening tool. Do not store raw descriptions longer than the team's
agreed policy; the model itself keeps no state and writes no logs.

## Versioning

- `0.1.0` (schema 1.0): first shipped artifact, 2026-11-23.
- Retraining rewrites `models/area_model.joblib`, `models/metadata.json` and
  `models/metrics.json`. Bump the package version when the contract or the feature
  pipeline changes.
