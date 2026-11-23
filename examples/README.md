# 예시

장문 경로 점검용으로 손으로 쓴 부모 말투 설명 3건입니다. **평가 데이터가 아닙니다.**
구현자가 영역별로 하나씩 썼고, 각각 의도한 영역이 1위로 나오는 것을 확인했습니다.

| 파일 | 의도한 영역 | 1위 |
|---|---|---|
| `inputs/parent_01_art.txt` | 예술경험 | 예술경험 (0.363) |
| `inputs/parent_02_social.txt` | 사회관계 | 사회관계 (0.421) |
| `inputs/parent_03_physical.txt` | 신체운동·건강 | 신체운동·건강 (0.585) |

`outputs/*.json`은 다음 명령의 stdout을 그대로 저장한 것입니다.

```sh
python -m nuri_mvp predict --file examples/inputs/parent_01_art.txt
```

재학습 후에는 다시 생성하고, 이 표를 정확도 근거로 제시하지 마세요.
