"""
Platform activity scoring.

Quantifies a candidate's platform engagement, visibility, credibility,
and availability based on Redrob platform signals. These behavioral
signals help identify candidates who are actively looking, responsive,
and credible - beyond just their technical skills.
"""

from typing import Dict, Any, Optional


def calculate_platform_score(
    redrob_signals: Optional[Dict[str, Any]] = None,
) -> float:
    """
    Score a candidate's platform activity and behavioral signals (0-100).

    Components:
    - Engagement (0-25): response rate, interview completion, activity
    - Visibility (0-25): profile completeness, recruiter interest
    - Credibility (0-25): verifications, GitHub, endorsements
    - Availability (0-25): open to work, notice period

    Parameters
    ----------
    redrob_signals : dict, optional
        Pre-computed redrob signals from Part 1 processing.

    Returns
    -------
    float
        Score in 0-100.
    """
    if not redrob_signals:
        return 40.0  # neutral default when no signals available

    engagement = redrob_signals.get("engagement_score", 0.0)
    visibility = redrob_signals.get("visibility_score", 0.0)
    credibility = redrob_signals.get("credibility_score", 0.0)
    availability = redrob_signals.get("availability_score", 0.0)

    # Weighted combination: engagement and availability matter most for hiring
    total = (
        engagement * 25 +
        visibility * 25 +
        credibility * 25 +
        availability * 25
    )

    return round(max(0, min(100, total)), 2)


def describe_platform_signals(
    redrob_signals: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Generate human-readable descriptions of platform signals.

    Returns
    -------
    dict with ``strengths`` and ``warnings`` lists.
    """
    strengths: list = []
    warnings: list = []

    if not redrob_signals:
        return {"strengths": ["No platform data available"], "warnings": []}

    # Engagement
    response_rate = redrob_signals.get("recruiter_response_rate", 0)
    if response_rate >= 0.7:
        strengths.append(f"High recruiter response rate ({response_rate:.0%})")
    elif response_rate >= 0.4:
        strengths.append(f"Moderate recruiter response rate ({response_rate:.0%})")
    elif response_rate > 0:
        warnings.append(f"Low recruiter response rate ({response_rate:.0%})")

    # Open to work
    if redrob_signals.get("open_to_work"):
        strengths.append("Currently open to work")

    # GitHub activity
    github = redrob_signals.get("github_activity_score", -1)
    if github >= 70:
        strengths.append(f"Strong GitHub activity (score: {github:.0f})")
    elif github >= 40:
        strengths.append(f"Active GitHub presence (score: {github:.0f})")
    elif github >= 0:
        warnings.append(f"Low GitHub activity (score: {github:.0f})")

    # Verification
    if redrob_signals.get("verified"):
        strengths.append("Fully verified profile (email + phone)")

    # Notice period
    notice = redrob_signals.get("notice_period_days", 30)
    if notice <= 15:
        strengths.append(f"Quick availability ({notice} days notice)")
    elif notice <= 30:
        strengths.append(f"Standard notice period ({notice} days)")
    elif notice > 60:
        warnings.append(f"Long notice period ({notice} days)")

    # Profile completeness
    completeness = redrob_signals.get("profile_completeness", 0)
    if completeness >= 90:
        strengths.append(f"Complete profile ({completeness:.0f}%)")
    elif completeness < 50:
        warnings.append(f"Incomplete profile ({completeness:.0f}%)")

    # Recruiter interest
    saved = redrob_signals.get("profile_views_received_30d", 0)
    if saved >= 50:
        strengths.append(f"High recruiter interest ({saved} profile views)")

    if not strengths:
        strengths.append("Has basic platform presence")

    return {"strengths": strengths, "warnings": warnings}
