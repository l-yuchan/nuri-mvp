"""Text normalization and segmentation of a long description into observations.

The area model was trained on single observation records (one or two sentences).
A parent description arrives as several paragraphs, so it is cut into
sentence-sized segments and each segment is scored separately.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Final

MIN_SEGMENT_CHARS: Final[int] = 8

_SENTENCE_END: Final[re.Pattern[str]] = re.compile(r"(?<=[.!?…\u3002\uff1f\uff01])\s+")


def normalize_syllables(text: str) -> str:
    """Compose Hangul, lowercase Latin letters and collapse whitespace."""
    return " ".join(unicodedata.normalize("NFC", text).lower().split())


def split_observations(text: str, *, min_chars: int = MIN_SEGMENT_CHARS) -> list[str]:
    """Split a description into sentence-level segments that can carry evidence.

    Lines are split first, then sentence-final punctuation. Segments shorter than
    ``min_chars`` (interjections, speaker labels) are dropped. When nothing
    survives, the whole stripped text is returned as one segment so that the
    caller still gets a prediction.
    """
    segments: list[str] = []
    for line in text.splitlines():
        for piece in _SENTENCE_END.split(line):
            candidate = piece.strip()
            if len(candidate) >= min_chars:
                segments.append(candidate)
    if segments:
        return segments
    whole = text.strip()
    return [whole] if whole else []


def segment_stats(text: str, segments: list[str]) -> dict[str, int]:
    """Return character and segment counts reported in the prediction payload."""
    return {
        "chars": len(text.strip()),
        "segments": len(segments),
    }
