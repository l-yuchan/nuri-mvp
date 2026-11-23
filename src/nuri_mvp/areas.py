"""The five Nuri areas and their short display descriptions."""

from __future__ import annotations

from typing import Final

AREAS: Final[tuple[str, ...]] = (
    "사회관계",
    "신체운동·건강",
    "예술경험",
    "의사소통",
    "자연탐구",
)

AREA_DESCRIPTIONS: Final[dict[str, str]] = {
    "사회관계": "자기 이해, 또래·성인과의 관계, 공동체 생활",
    "신체운동·건강": "신체활동, 건강한 생활, 안전한 생활",
    "예술경험": "아름다움 탐색, 창의적 표현, 예술 감상",
    "의사소통": "듣기와 말하기, 읽기와 쓰기, 언어 사용 태도",
    "자연탐구": "주변 사물과 자연 탐구, 수학적·과학적 사고",
}
