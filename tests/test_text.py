"""Segmentation behaviour for long parent descriptions."""

import pytest

from nuri_mvp.text import MIN_SEGMENT_CHARS, normalize_syllables, split_observations


def test_splits_paragraphs_and_sentences() -> None:
    text = "첫째 문장은 충분히 깁니다. 둘째 문장도 충분히 깁니다.\n셋째 문장입니다."
    assert split_observations(text) == [
        "첫째 문장은 충분히 깁니다.",
        "둘째 문장도 충분히 깁니다.",
        "셋째 문장입니다.",
    ]


def test_drops_short_fragments() -> None:
    text = "네. 아이가 블록을 높이 쌓았습니다. 응."
    segments = split_observations(text)
    assert segments == ["아이가 블록을 높이 쌓았습니다."]
    assert all(len(segment) >= MIN_SEGMENT_CHARS for segment in segments)


def test_falls_back_to_whole_text_without_punctuation() -> None:
    text = "아이가 계속 웃으면서 블록을 옮기고 친구에게 건네주는 모습을 보였다"
    assert split_observations(text) == [text]


def test_blank_text_has_no_segments() -> None:
    assert split_observations("   \n  ") == []


def test_normalization_composes_and_lowercases() -> None:
    assert normalize_syllables("  ABC  하늘\t색  ") == "abc 하늘 색"


@pytest.mark.parametrize("text", ["", " ", "\n\n"])
def test_whitespace_only_is_not_scorable(text: str) -> None:
    assert split_observations(text) == []
