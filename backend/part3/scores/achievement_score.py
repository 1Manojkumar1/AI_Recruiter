"""
Achievement impact scoring.

Quantifies a candidate's measurable achievements including promotions,
leadership, awards, patents, open-source contributions, publications,
and large-scale project impact.
"""

from typing import Dict, Any, List


def calculate_achievement_score(
    leadership_score: float = 0.0,
    impact_score: float = 0.0,
    promotion_count: int = 0,
    career_growth_score: float = 0.0,
    profile_text: str = "",
) -> float:
    """
    Score a candidate's achievement impact (0-100).

    Scoring components:
    - Leadership evidence (0-25 points)
    - Impact/ measurable outcomes (0-25 points)
    - Career progression / promotions (0-25 points)
    - Keyword-detected achievements (0-25 points)

    Parameters
    ----------
    leadership_score : float
        0-1 leadership evidence from Part 1.
    impact_score : float
        0-1 impact evidence from Part 1.
    promotion_count : int
        Number of detected promotions.
    career_growth_score : float
        0-1 career growth score from Part 1.
    profile_text : str
        Combined text from profile, career history (for keyword scanning).

    Returns
    -------
    float
        Score in 0-100.
    """
    # Leadership component (0-25)
    leadership_pts = leadership_score * 25

    # Impact component (0-25)
    impact_pts = impact_score * 25

    # Promotion component (0-25)
    promo_pts = min(25.0, promotion_count * 8.33)

    # Keyword-detected achievements (0-25)
    keyword_pts = _scan_achievement_keywords(profile_text) * 25

    total = leadership_pts + impact_pts + promo_pts + keyword_pts
    return round(max(0, min(100, total)), 2)


def _scan_achievement_keywords(text: str) -> float:
    """
    Scan text for achievement-related keywords and return a 0-1 score.

    Keywords are grouped by impact level.
    """
    if not text:
        return 0.0

    lower = text.lower()

    high_impact = [
        "patent", "published", "publication", "award", "recognised",
        "recognized", "led team", "managed team", "direct report",
        "scaled to", "million users", "billion", "revenue",
    ]

    medium_impact = [
        "promoted", "promotion", "built scalable", "reduced latency",
        "improved performance", "saved costs", "increased revenue",
        "deployed", "launched", "shipped", "migrated", "transformed",
        "mentored", "coaching", "tech lead", "team lead",
    ]

    low_impact = [
        "automated", "streamlined", "optimized", "delivered",
        "implemented", "designed", "led", "managed", "supervised",
        "oversaw", "guided", "coordinated",
    ]

    high_hits = sum(1 for kw in high_impact if kw in lower)
    medium_hits = sum(1 for kw in medium_impact if kw in lower)
    low_hits = sum(1 for kw in low_impact if kw in lower)

    # Weighted score
    raw = (high_hits * 0.4 + medium_hits * 0.3 + low_hits * 0.3) / 8.0
    return max(0.0, min(1.0, raw))


def describe_achievements(
    leadership_score: float = 0.0,
    impact_score: float = 0.0,
    promotion_count: int = 0,
    profile_text: str = "",
) -> Dict[str, List[str]]:
    """
    Generate human-readable achievement descriptions.

    Returns
    -------
    dict with ``strengths`` and ``all_achievements`` lists.
    """
    strengths: List[str] = []
    achievements: List[str] = []

    if leadership_score >= 0.6:
        strengths.append("Strong leadership experience managing teams")
        achievements.append("Led and managed engineering teams")
    elif leadership_score >= 0.3:
        strengths.append("Some leadership experience")
        achievements.append("Demonstrated people management skills")

    if impact_score >= 0.5:
        strengths.append("Strong track record of measurable impact")
        achievements.append("Delivered significant business outcomes")
    elif impact_score >= 0.2:
        strengths.append("Evidence of business impact")
        achievements.append("Contributed to measurable results")

    if promotion_count >= 3:
        strengths.append(f"Fast career progression ({promotion_count} promotions)")
        achievements.append(f"Received {promotion_count} promotions")
    elif promotion_count >= 1:
        strengths.append(f"Career progression ({promotion_count} promotion{'s' if promotion_count > 1 else ''})")
        achievements.append(f"Received {promotion_count} promotion{'s' if promotion_count > 1 else ''}")

    # Scan for specific keywords
    if profile_text:
        lower = profile_text.lower()
        if "patent" in lower:
            achievements.append("Has patent(s)")
            strengths.append("Patent holder")
        if "published" in lower or "publication" in lower:
            achievements.append("Has publications")
            strengths.append("Published researcher")
        if "open source" in lower or "github" in lower:
            achievements.append("Open source contributor")

    return {
        "strengths": strengths,
        "all_achievements": achievements,
    }
