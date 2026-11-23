# 예측 계약 (스키마 1.0)

통합 시스템은 함수 하나를 호출하고 JSON 객체 하나를 읽습니다. 런타임에 이 저장소에서
필요한 것은 `models/` 디렉터리뿐입니다.

## 진입점

| 형태 | 호출 | 비고 |
|---|---|---|
| Python | `Predictor.from_dir("models").predict(text)` | 권장. 시작할 때 한 번 로드 |
| Python | `Predictor(model).predict_batch([...])` | 입력마다 `predict`를 호출 |
| CLI | `python -m nuri_mvp predict --text ...` 또는 `--file path` | 같은 JSON을 stdout으로 출력 |

`predict`는 순수 함수입니다. 같은 텍스트를 넣으면 같은 결과가 나오고 세션 상태를
유지하지 않습니다. 같은 아동의 여러 설명을 합치는 일은 통합 쪽에서 하거나, 호출 전에
텍스트를 이어 붙이면 됩니다.

## 입력

- 문자열 하나, UTF-8, 길이 제한 없음. 줄바꿈과 문장부호(`.!?…。？！`)가 분절 경계입니다.
- 8자 미만 문장 조각은 버립니다(감탄사, 화자 라벨).
- 남는 문장이 없으면(문장부호 없음, 아주 짧은 텍스트) 공백을 제거한 전체 텍스트를
  한 문장으로 채점합니다.
- 빈 문자열이나 공백만 있는 입력은 `ValueError`를 냅니다. CLI는
  `{"error": "input text is empty"}`를 출력하고 종료 코드 2를 반환합니다.

## 출력

| 필드 | 타입 | 의미 |
|---|---|---|
| `schema_version` | string | `"1.0"`. 호환성이 깨지면 올립니다 |
| `strongest_area` | string | 평균 확률이 가장 높은 영역 |
| `second_area` | string | 두 번째. `strongest_area`와 절대 같지 않음 |
| `weakest_area` | string | 순위 마지막. **실험적** 필드. 판단으로 검증되지 않았으니 평가처럼 제시하지 마세요 |
| `areas` | 5개 객체 배열 | `{rank, area, probability}`, 확률 내림차순, 합은 1(소수점 6자리 반올림) |
| `confidence.top1_probability` | float | `strongest_area`의 확률 |
| `confidence.gap_top1_top2` | float | `top1 - top2`. 작으면 두 후보가 비슷함 |
| `segments.used` | int | 채점한 문장 수 |
| `segments.chars` | int | 공백 제거 후 입력 길이 |
| `segments.aggregation` | string | 항상 `"mean_area_probability"` |
| `model.name` | string | 모델 식별자 |
| `model.trained_at` | string | 배포 아티팩트의 학습 시각 (ISO-8601 UTC) |
| `model.data_sha256` | object | 학습에 쓴 CSV 해시 |

영역 이름은 정확히 `사회관계`, `신체운동·건강`, `예술경험`, `의사소통`, `자연탐구`입니다.

## 통합이 지켜야 할 의미 규칙

1. `strongest_area`는 해당 설명에 대해 모델이 고른 최선의 영역입니다. 검증 수준에서
   정답 영역과 일치하는 비율이 71.5%입니다.
2. `second_area`는 다음 후보입니다. **1·2위의 순서 자체는 검증되지 않았습니다.**
   top-2 정확도는 "정답이 둘 중 하나였다"만 말합니다. 화면 문구는
   "가장 두드러지는 영역 + 다음 후보"로 쓰고, "1등 영역, 2등 영역"처럼 쓰지 마세요.
3. 확률은 문장별로 보정한 뒤 평균한 값이라 한 응답 안에서는 비교할 수 있지만,
   응답 사이·아동 사이 비교에는 쓰지 마세요.
4. `weakest_area`는 정보성 필드입니다. 발달 판단으로 보여주지 마세요.
5. 기권이 없습니다. 짧거나 주제를 벗어난 텍스트도 확률 5개를 돌려줍니다.

## 지연과 배포

| 단계 | 측정값 |
|---|---|
| `Predictor.from_dir` (콜드) | 186ms |
| 200~400자 설명 `predict` | 중앙값 5.0ms, p95 6.3ms |
| 아티팩트 크기 | 4.8MB joblib |

전부 CPU에서 돕니다. 데모 대상이 랩탑이므로 장치 전용 경로는 필요 없습니다.
`Predictor` 인스턴스 하나면 충분하고, 여러 스레드에서 동시에 호출하는 경우는
검증하지 않았습니다.

## 호환성

아티팩트는 scikit-learn 1.9.1 / joblib 1.6.0으로 만들어졌습니다(기준 환경 Python 3.14,
`requires-python >= 3.11`). 통합 환경의 scikit-learn을 같은 minor 계열로 고정하거나,
스택이 다르면 CLI를 서브프로세스로 호출하세요.

## 오류

| 상황 | Python | CLI |
|---|---|---|
| 빈 텍스트 | `ValueError("input text is empty")` | 종료 2, `{"error": ...}` |
| 채점할 문장 없음 | `ValueError("input text has no scorable segment")` | 종료 2 |
| 모델 디렉터리 없음 | `FileNotFoundError` | 종료 2 |
| 학습 시 CSV 누수·스키마 문제 | `nuri_mvp.model.DataError` | 종료 2 |
