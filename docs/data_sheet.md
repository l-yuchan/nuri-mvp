# Data sheet

Scope: the two CSVs shipped in `data/` and the model derived from them. This is not a
complete dataset release and the files must not be redistributed outside the
team / course context.

## Contents

| File | Rows | Columns used by this repo | sha256 |
|---|---:|---|---|
| `train.csv` | 666 | `id, text, label, group_id, source` | `810703446f63c7f3ceafff783469e0bcdfce2729291321ba611d7662b3640c2c` |
| `val.csv` | 158 | same | `21c2976c7aa2ec253fc61acb3c74b635faff8db40c35b3c5088e95fc9aac6982` |

Both files carry more columns than this repo uses (`session, content_category,
item_no, item_text, context, level, age, label_source, use_default, split, note`).
`level` and `item_text` exist only for KICCE rows and are not used here.

## Provenance

- **KICCE 유아관찰척도 관찰사례** (scale vignettes): 704 rows overall (572 train /
  132 val). Each indicator group contains 12 vignettes, three per developmental level
  (1-4). The label is the area of the assessed **indicator**, not the dominant theme
  of the vignette text.
- **교육부·보건복지부 놀이 사례집 발췌** (2020): 120 rows overall (94 train / 26 val),
  page-level groups (`CB-p3xx`), mixed labels within a page group.
- Both were extracted by the team for the course project. They are **institute and
  public documents, not team-collected field data**. No parent, teacher or child was
  recorded or interviewed for these files.

## Split

- Group-disjoint by `group_id`: no group appears in both splits. The loader enforces
  this and also rejects identical normalized text across splits.
- `val.csv` has 13 groups (11 KICCE indicator groups + 2 casebook pages).
- The split is fixed for the project; this repository never reshuffles it.
- Splitting by session/date is not applicable to extracted documents; the session
  column records the extraction batch, not a data-collection session.

## Label definition and known ambiguity

One label per row, five areas. For KICCE rows the gold label follows the assessed
indicator, so the same scene can look like another area to a reader. Documented
problem groups from the probe study in the experiment repository:

- `KI-4-02` (예술경험, leaf-texture scenes): external judges chose 자연탐구 in 65% of
  cases.
- `KI-2-05` (의사소통, sketchbook conflict): 48% chose 사회관계.
- `KI-3-04` (사회관계, family scene): 40% wrong; this is also the weakest validation
  group (17% row accuracy).
- `KI-3-12` (사회관계, other-culture greeting): read as 의사소통 by both human and
  LLM probes.

Label quality overall was judged defensible: gold-label plausibility 4.2-4.6 out of 5
across four LLM runs, with only 5 items flagged by all four.

## What is missing

- **No team-collected data.** The course rubric asks for at least some data collected
  in or near the use environment. Not satisfied by this repository.
- **No double labeling / inter-annotator agreement.** There is no labeling protocol
  file and no second annotator.
- **No test set.** `val.csv` doubles as the reporting split and was used for model
  selection in the experiment repository.
- **No parent-speech data.** Descriptions here are written observation records, not
  transcribed parent speech.
- No age or setting metadata is used; casebook rows carry `age` inconsistently.

## Privacy

The text describes children's behavior but contains no names or identifiers in the
shipped files (only `N###` ids). Speech transcripts produced by the integration are
not part of this dataset and must follow the team's consent/retention policy.
