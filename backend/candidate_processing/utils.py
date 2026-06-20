"""
Utility helpers shared across the candidate processing pipeline.
"""

import re
import math
from typing import Optional, List


def safe_float(value: Optional[float], default: float = 0.0) -> float:
    """Return *value* if finite, otherwise *default*."""
    if value is None or (isinstance(value, float) and (math.isnan(value) or math.isinf(value))):
        return default
    return float(value)


def safe_int(value: Optional[int], default: int = 0) -> int:
    """Return *value* as int if possible, otherwise *default*."""
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def normalize_whitespace(text: str) -> str:
    """Collapse runs of whitespace into single spaces and strip."""
    return re.sub(r"\s+", " ", text).strip()


def clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """Clamp *value* between *lo* and *hi*."""
    return max(lo, min(hi, value))


def extract_percentage(text: str) -> Optional[float]:
    """
    Try to pull a numeric percentage from text like '85%' or '8.60 CGPA'.
    Returns None when nothing parseable is found.
    """
    match = re.search(r"(\d+(?:\.\d+)?)\s*%", text)
    if match:
        return float(match.group(1))

    match = re.search(r"(\d+(?:\.\d+)?)\s*CGPA", text, re.IGNORECASE)
    if match:
        return float(match.group(1)) * 10.0  # assume /10 scale

    match = re.search(r"(\d+(?:\.\d+)?)", text)
    if match:
        val = float(match.group(1))
        if val <= 10.0:
            return val * 10.0
        return val
    return None


def text_contains_any(text: str, keywords: List[str]) -> bool:
    """Return True if *text* (lowered) contains any of the *keywords*."""
    lowered = text.lower()
    return any(kw in lowered for kw in keywords)


def count_keyword_hits(text: str, keywords: List[str]) -> int:
    """Count how many distinct *keywords* appear in *text*."""
    lowered = text.lower()
    return sum(1 for kw in keywords if kw in lowered)
