"""
Experience match scoring.

Compares a candidate's years of experience against the job requirement
using a smooth scoring curve that rewards meeting or exceeding the
requirement while not overly penalising slight shortfalls.
"""

import math
from typing import Dict, Any, Optional


def calculate_experience_score(
    candidate_years: float,
    required_years: int,
    candidate_seniority: str = "",
    required_seniority: str = "",
    leadership_score: float = 0.0,
) -> float:
    """
    Score experience match (0-100).

    Scoring curve:
    - Meets/exceeds requirement: 85-100 (diminishing returns above 1.5x)
    - Slightly below (70-99% of required): 60-85
    - Notably below (40-69%): 30-60
    - Far below (<40%): 0-30

    Also considers seniority level match and leadership experience.

    Parameters
    ----------
    candidate_years : float
        Candidate's total years of experience.
    required_years : int
        Job-required years (0 = unspecified).
    candidate_seniority : str
        Candidate's seniority level.
    required_seniority : str
        Job-required seniority level.
    leadership_score : float
        0-1 leadership evidence score.

    Returns
    -------
    float
        Score in 0-100.
    """
    # Base experience score
    base = _calculate_base_experience_score(candidate_years, required_years)

    # Seniority bonus
    seniority_bonus = _calculate_seniority_bonus(candidate_seniority, required_seniority)

    # Leadership bonus (up to 5 points)
    leadership_bonus = min(5.0, leadership_score * 5.0)

    score = base + seniority_bonus + leadership_bonus
    return round(max(0, min(100, score)), 2)


def _calculate_base_experience_score(candidate_years: float, required_years: int) -> float:
    """Calculate base score from years of experience."""
    if required_years <= 0:
        # No requirement specified: score based on experience alone
        if candidate_years >= 10:
            return 85.0
        if candidate_years >= 5:
            return 75.0
        if candidate_years >= 2:
            return 65.0
        return 50.0

    ratio = candidate_years / required_years

    if ratio >= 1.0:
        # Meets or exceeds: 85-100 with diminishing returns
        score = 85 + 15 * (1 - math.exp(-(ratio - 1) * 0.5))
    elif ratio >= 0.7:
        # Slightly below: 60-85
        score = 60 + 25 * (ratio - 0.7) / 0.3
    elif ratio >= 0.4:
        # Notably below: 30-60
        score = 30 + 30 * (ratio - 0.4) / 0.3
    else:
        # Far below: 0-30
        score = max(0, 30 * ratio / 0.4)

    return score


def _calculate_seniority_bonus(candidate: str, required: str) -> float:
    """Calculate bonus/penalty from seniority level comparison."""
    if not candidate or not required:
        return 0.0

    from ..utils.weights import SENIORITY_LEVELS

    c = SENIORITY_LEVELS.get(candidate.lower().strip(), 0)
    r = SENIORITY_LEVELS.get(required.lower().strip(), 0)

    if c == 0 or r == 0:
        return 0.0

    diff = c - r
    if diff == 0:
        return 5.0  # exact match bonus
    if diff == 1:
        return 3.0  # slightly overqualified
    if diff >= 2:
        return 2.0  # overqualified (still good)
    if diff == -1:
        return 0.0  # slightly under
    return -5.0  # significantly under
