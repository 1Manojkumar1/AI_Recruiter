"""
Career growth scoring.

Evaluates the candidate's career trajectory based on growth signals
from Part 1 output.
"""


def calculate_growth_score(career_growth_score: float, promotion_count: int) -> float:
    """
    Score career growth trajectory.

    Parameters
    ----------
    career_growth_score : float
        0-1 growth score from Part 1.
    promotion_count : int
        Number of detected promotions.

    Returns
    -------
    float
        Score in 0-100.
    """
    # Base from Part 1 growth score (0-70 points)
    base = career_growth_score * 70

    # Promotion bonus (0-30 points)
    promo_bonus = min(30, promotion_count * 10)

    total = base + promo_bonus
    return round(min(100, max(0, total)), 2)
