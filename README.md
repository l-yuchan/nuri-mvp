# 누리 영역 MVP

아동에 대한 장문 한국어 설명 -> **가장 강한 누리 영역**과 **두 번째 영역**.

이 저장소는 통합 시스템을 위한 ML 산출물입니다. 일부러 작게 유지했습니다: 분류기 하나,
아티팩트 하나, JSON 계약 하나, 실험 코드 없음. 실험 기록(비교한 모든 대안, 프로브,
항목 단위 작업)은 `ml/` 실험 디렉터리에 그대로 두었고, 요약은
[docs/findings.md](docs/findings.md)에 있습니다.

```
설명 텍스트
   -> 문장 단위 분절
   -> 문장별 5개 영역 확률 (보정된 SVM)
   -> 문장 평균
   -> 영역 순위, strongest / second / weakest
```

## 현재 성능

데이터에 포함된 검증 분할: 13개 지표 그룹의 158행 (`data/val.csv`,
`models/metrics.json`).

| 지표 | 값 |
|---|---:|
| top-1 영역 정확도 | 0.7152 |
| Macro-F1 | 0.7087 |
| top-2 정확도 (정답이 1-2위 안) | 0.8924 |

탐색적 검증 점수이며, `ml/`에서 설정 선택에 쓴 것과 같은 분할입니다. 별도 테스트셋은
아직 없습니다. 장문 경로(분절+평균)는 이 수치에 포함되지 않습니다. 손으로 쓴 예시
3건으로만 확인했습니다([examples/](examples/)). 수치를 인용하기 전에
[docs/model_card.md](docs/model_card.md)를 읽어 주세요.

## 빠른 시작

Python 3.11 이상.

```sh
uv venv
uv pip install -e ".[dev]"
uv run python -m nuri_mvp evaluate     # 저장된 아티팩트를 data/val.csv로 채점
uv run pytest                          # 23개 테스트, 0.7152 재현 검사 포함
```

uv가 없다면:

```sh
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"
.venv/Scripts/python -m nuri_mvp evaluate
```

`data/train.csv`로 재학습은 몇 초면 되고 결과가 재현됩니다:

```sh
uv run python -m nuri_mvp train        # models/area_model.joblib + metadata 재작성
```

## 사용법

```python
from nuri_mvp import Predictor

predictor = Predictor.from_dir("models")  # 시작할 때 한 번
result = predictor.predict("아이가 색종이를 오려 ...")  # 길이 제한 없는 한국어 텍스트

result["strongest_area"]  # "예술경험"
result["second_area"]  # "사회관계"
result["areas"]  # 5개 영역 전체, 확률과 함께 순위
```

명령줄:

```sh
uv run python -m nuri_mvp predict --file examples/inputs/parent_01_art.txt
uv run python -m nuri_mvp predict --text "아이가 블록으로 높은 탑을 쌓았습니다."
```

응답 예시 (`examples/outputs/parent_01_art.json`, 일부):

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

필드별 계약, 오류 동작, 통합 방법은 [docs/interface.md](docs/interface.md)에 있습니다.

이 장비(CPU)에서 측정: 모델 로드 186ms(한 번), 추론 중앙값 5.0ms, p95 6.3ms.

## 하지 않는 것

- 항목(지표) 단위 출력, 발달 수준 1-4, 활동 추천, 지도 LED, 음성 입력은 범위 밖입니다.
- "근거 없음" 기권 판정이 없습니다. 비어 있지 않은 입력은 항상 순위를 냅니다.
  `weakest_area`는 순위의 부산물이며 판단으로 검증되지 않았습니다.
- 한국어 텍스트 전용이고, 실제 부모 발화·전사문으로는 평가된 적이 없습니다.

## 저장소 구조

```
data/           train.csv, val.csv (고정 분할, docs/data_sheet.md 참고)
models/         배포 아티팩트 (joblib 약 4.8MB) + metadata.json + metrics.json
src/nuri_mvp/   areas.py, text.py, model.py, pipeline.py, cli.py
tests/          분절, 계약, 재학습 재현 테스트
examples/       손으로 쓴 장문 3건 + 실제 출력 JSON
docs/           interface.md, model_card.md, data_sheet.md, findings.md
```

## 데이터 주의

데이터셋은 과목 프로젝트용으로 제공된 KICCE 관찰척도와 교육부 사례집 발췌입니다.
CSV와 파생 모델을 팀·과목 범위 밖으로 공개하지 마세요.
[docs/data_sheet.md](docs/data_sheet.md)를 참고하세요.
