"""
Experience matching engine.

Compares the candidate's years of experience against the job requirement
using a smooth scoring curve.
"""

import math


def calculate_experience_score(candidate_years: float, required_years: int) -> float:
    """
    Score experience match.

    - If candidate meets or exceeds requirement: high score (up to 100).
    - If candidate is slightly below: moderate score.
    - If candidate is far below: low score.

    Parameters
    ----------
    candidate_years : float
        Candidate's total years of experience.
    required_years : int
        Job-required years (0 = unspecified).

    Returns
    -------
    float
        Score in 0-100.
    """
    if required_years <= 0:
        return 75.0  # neutral when not specified

    ratio = candidate_years / required_years

    if ratio >= 1.0:
        # Meets or exceeds: 85-100 based on how much they exceed
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

    return round(min(100, max(0, score)), 2)
