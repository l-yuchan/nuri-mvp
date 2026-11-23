# Examples

Three hand-written parent-style descriptions used as a smoke check of the long-text
path. They are **not** evaluation data: they were written by the implementer, one per
intended area, and each is expected to return its intended area at rank 1.

| File | Intended area | Rank 1 |
|---|---|---|
| `inputs/parent_01_art.txt` | 예술경험 | 예술경험 (0.363) |
| `inputs/parent_02_social.txt` | 사회관계 | 사회관계 (0.421) |
| `inputs/parent_03_physical.txt` | 신체운동·건강 | 신체운동·건강 (0.585) |

`outputs/*.json` is the exact stdout of:

```sh
python -m nuri_mvp predict --file examples/inputs/parent_01_art.txt
```

Re-generate them after retraining, and do not present this table as accuracy evidence.
