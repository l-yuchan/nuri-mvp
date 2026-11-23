# Findings behind this MVP

This file records why the shipped model is the shipped model, and which numbers may
be quoted. The full experiment record lives in the sibling directory `ml/`
(`EXPERIMENTS.md`, `HIERARCHICAL.md`, `CHILD_PROFILE.md`, `INDICATOR_LINKING.md`,
`ABLATION.md`, `probes/`). Nothing here was re-run for this repository except the
final training, which reproduced the validation score exactly.

## 1. Model comparison on the same fixed split

Best configuration per representation family, 666 train / 158 val, selected on
validation Macro-F1 in the experiment repository:

| Representation | Setting | Accuracy | Macro-F1 | Top-2 |
|---|---|---:|---:|---:|
| **Character 2-5 TF-IDF + calibrated LinearSVC** | C=10, sigmoid, group-aware CV | **0.7152** | **0.7087** | **0.8924** |
| Character 2-5 TF-IDF + LinearSVC (uncalibrated) | C=10 | 0.6899 | 0.6798 | 0.8734 |
| Character 2-5 TF-IDF + logistic regression | C=10 | 0.6519 | 0.6420 | 0.8671 |
| Jamo 3-8 TF-IDF + LinearSVC | C=1 | 0.6329 | 0.6286 | 0.8671 |
| Supervised fastText, random init | 100 epochs | 0.6266 | 0.6148 | 0.8544 |
| Supervised fastText, web-corpus init | 100 epochs | 0.5570 | 0.5500 | 0.8038 |
| Frozen multilingual-E5-small + LinearSVC | C=1 | 0.5253 | 0.5113 | 0.7722 |
| fastText CBOW sentence vectors + logistic | C=10 | 0.4114 | 0.4181 | 0.6139 |

The calibration step is a real gain (+2.7 points accuracy, +4.9 points top-2) and is
cheap. Semantic representations did not help on this data size; the 25-run ablation
showed that the web-corpus initialization benefit was a vector-norm effect
(shuffled vectors scored identically), and no configuration beat the TF-IDF model.

## 2. Why long text is segmented and averaged

The model was trained on single observation records. The MVP must consume a long
description. Two facts from the experiment repository support the segmentation +
mean-probability design:

- The child-profile experiment showed that pooling more observations of the same item
  improves within-child ranking monotonically (m=1: NDCG@2 0.80, QWK 0.58; m=3:
  0.88, 0.74). Averaging, not taking one segment, is the better estimator.
- The probe study showed that single-vignette ambiguity is structural for a few
  indicator groups, so averaging a few independent sentences reduces the chance that
  one ambiguous sentence decides the result.

This is a design argument, not a measured result: the long-text path has only been
exercised on three hand-written examples (`examples/`), each of which returns its
intended area at rank 1. Treat that as a smoke check, not an accuracy claim.

## 3. What the numbers do and do not mean

- **Top-1 0.7152**: the gold area equals the highest-probability area for 71.5% of
  validation records. Group-mean accuracy is 0.713 over 13 groups (worst 0.167), so
  row-level accuracy overstates independent-trial precision.
- **Top-2 0.8924**: the gold area appears among the top two. It says nothing about
  whether the second area is the "second strongest" in any real sense. The contract
  therefore calls it a candidate.
- **Calibration**: sigmoid calibration of a linear SVM; probabilities are usable for
  comparison inside one response. Mean confidence when correct was 0.573 vs 0.515 when
  wrong, so confidence separates errors only weakly.
- **Selection leak**: `val.csv` selected the configuration in `ml/`. A true held-out
  test set does not exist. If a test set is later carved out, do not reuse this
  repository's metrics as the comparison baseline without recomputing.

## 4. Item-level work that is intentionally not in this MVP

The experiment repository went further than area classification. None of it is part of
this contract, but the results explain why the MVP stops at areas:

| Topic | Result | Why out of scope |
|---|---|---|
| Observation -> indicator linking (59 candidates) | Frozen E5 zero-shot Recall@1 24.2%; char TF-IDF 19.7%; trained projections 1.5-5.9% | Too weak to drive a demo; training on seen indicators destroys unseen transfer |
| Developmental level 1-4 | 56.1% exact, ±1 85.6%, QWK 0.576 | Not requested for this MVP; 3 is a boundary (21% exact) |
| Synthetic child profile (item levels + strong/weak items) | NDCG@2 0.88 with oracle links, 0.16-0.27 with predicted links | The linking bottleneck makes the end-to-end number unusable |
| Recommendation / LED mapping | Not implemented anywhere | Explicitly outside the current interest |

If a later version needs item-level output, the order of work is: improve linking
without fitting on seen indicators, then re-run the profile evaluation. Adding a level
head or more training does not fix the linking bottleneck.

## 5. Reproduction

```sh
uv run python -m nuri_mvp train     # rewrites models/, prints validation summary
uv run python -m nuri_mvp evaluate  # re-scores the shipped artifact
uv run pytest                       # includes a retrain check against 0.7152 / 0.8924
```

`models/metadata.json` records the seed, library versions, parameters and the sha256
of both CSVs, so a teammate can confirm the artifact matches `data/`.

## 6. References

- `../ml/EXPERIMENTS.md` - consolidated experiment results and metric definitions.
- `../ml/HIERARCHICAL.md` - area + level system and anti-confound checks.
- `../ml/CHILD_PROFILE.md` - aggregation evidence (NDCG/QWK vs number of observations).
- `../ml/INDICATOR_LINKING.md` - item linking protocol, zero-shot results, limits.
- `../ml/probes/analysis.md` - label-quality probes (LLM + human).
