"""
Achievement impact scoring.

Quantifies a candidate's measurable achievements from career data.
"""

from typing import Dict, Any


def calculate_achievement_score(
    leadership_score: float,
    impact_score: float,
    promotion_count: int,
) -> float:
    """
    Score a candidate's achievement impact.

    Parameters
    ----------
    leadership_score : float
        0-1 leadership evidence from Part 1.
    impact_score : float
        0-1 impact evidence from Part 1.
    promotion_count : int
        Number of detected promotions.

    Returns
    -------
    float
        Score in 0-100.
    """
    # Leadership component (0-40 points)
    leadership_pts = leadership_score * 40

    # Impact component (0-35 points)
    impact_pts = impact_score * 35

    # Promotion component (0-25 points)
    promo_pts = min(25, promotion_count * 8.33)

    total = leadership_pts + impact_pts + promo_pts
    return round(min(100, max(0, total)), 2)


def describe_achievements(
    leadership_score: float,
    impact_score: float,
    promotion_count: int,
) -> list:
    """Generate human-readable achievement descriptions."""
    descriptions = []
    if leadership_score >= 0.5:
        descriptions.append("Demonstrated strong leadership managing teams")
    elif leadership_score >= 0.2:
        descriptions.append("Some leadership experience")

    if impact_score >= 0.5:
        descriptions.append("Strong track record of measurable impact")
    elif impact_score >= 0.2:
        descriptions.append("Evidence of business impact")

    if promotion_count >= 3:
        descriptions.append(f"Fast career progression ({promotion_count} promotions)")
    elif promotion_count >= 1:
        descriptions.append(f"Career progression ({promotion_count} promotion{'s' if promotion_count > 1 else ''})")

    return descriptions
