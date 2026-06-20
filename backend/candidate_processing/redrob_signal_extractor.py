"""
Redrob Platform Signal Extractor.

Extracts and normalizes platform activity signals from the redrob_signals
field. These behavioral signals help rank candidates beyond just skills
and experience - they indicate engagement, availability, and recruiter
interest.
"""

from typing import Dict, Any


def extract_redrob_signals(redrob_signals: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract and normalize redrob platform signals into scoring-ready metrics.

    Parameters
    ----------
    redrob_signals : dict
        Raw redrob_signals from the candidate JSONL.

    Returns
    -------
    dict with normalized signals and derived scores.
    """
    if not redrob_signals:
        return _empty_signals()

    # --- Core signals ---
    profile_completeness = redrob_signals.get("profile_completeness_score", 0)
    open_to_work = redrob_signals.get("open_to_work_flag", False)
    response_rate = redrob_signals.get("recruiter_response_rate", 0)
    avg_response_time = redrob_signals.get("avg_response_time_hours", 48)
    github_score = redrob_signals.get("github_activity_score", -1)
    profile_views = redrob_signals.get("profile_views_received_30d", 0)
    applications = redrob_signals.get("applications_submitted_30d", 0)
    saved_by_recruiters = redrob_signals.get("saved_by_recruiters_30d", 0)
    interview_completion = redrob_signals.get("interview_completion_rate", 0)
    offer_acceptance = redrob_signals.get("offer_acceptance_rate", -1)
    notice_period = redrob_signals.get("notice_period_days", 30)
    connection_count = redrob_signals.get("connection_count", 0)
    endorsements = redrob_signals.get("endorsements_received", 0)
    search_appearance = redrob_signals.get("search_appearance_30d", 0)
    verified_email = redrob_signals.get("verified_email", False)
    verified_phone = redrob_signals.get("verified_phone", False)
    linkedin = redrob_signals.get("linkedin_connected", False)
    preferred_work_mode = redrob_signals.get("preferred_work_mode", "flexible")
    willing_to_relocate = redrob_signals.get("willing_to_relocate", False)

    # --- Derived scores ---

    # Engagement score (0-1): how active and responsive
    engagement = _compute_engagement(
        response_rate=response_rate,
        avg_response_time=avg_response_time,
        interview_completion=interview_completion,
        profile_views=profile_views,
        applications=applications,
    )

    # Visibility score (0-1): how visible to recruiters
    visibility = _compute_visibility(
        profile_views=profile_views,
        saved_by_recruiters=saved_by_recruiters,
        search_appearance=search_appearance,
        profile_completeness=profile_completeness,
    )

    # Credibility score (0-1): trust signals
    credibility = _compute_credibility(
        verified_email=verified_email,
        verified_phone=verified_phone,
        linkedin=linkedin,
        github_score=github_score,
        endorsements=endorsements,
        connection_count=connection_count,
    )

    # Availability score (0-1): how quickly available
    availability = _compute_availability(
        open_to_work=open_to_work,
        notice_period=notice_period,
        offer_acceptance=offer_acceptance,
    )

    # Platform activity score (composite)
    platform_score = round(
        0.30 * engagement + 0.25 * visibility +
        0.25 * credibility + 0.20 * availability, 4
    )

    return {
        "engagement_score": round(engagement, 4),
        "visibility_score": round(visibility, 4),
        "credibility_score": round(credibility, 4),
        "availability_score": round(availability, 4),
        "platform_activity_score": round(platform_score, 4),
        "open_to_work": open_to_work,
        "recruiter_response_rate": round(response_rate, 4),
        "notice_period_days": notice_period,
        "github_activity_score": github_score,
        "profile_completeness": profile_completeness,
        "verified": verified_email and verified_phone,
    }


def _compute_engagement(
    response_rate: float,
    avg_response_time: float,
    interview_completion: float,
    profile_views: int,
    applications: int,
) -> float:
    """Score candidate engagement 0-1."""
    # Response rate component (0-0.35)
    resp_score = min(response_rate, 1.0) * 0.35

    # Response speed (0-0.25): faster = better, capped at 24h
    if avg_response_time <= 0:
        speed = 0.5
    elif avg_response_time <= 4:
        speed = 1.0
    elif avg_response_time <= 12:
        speed = 0.8
    elif avg_response_time <= 24:
        speed = 0.6
    elif avg_response_time <= 48:
        speed = 0.4
    else:
        speed = 0.2
    speed_score = speed * 0.25

    # Interview completion (0-0.25)
    interview_score = min(interview_completion, 1.0) * 0.25

    # Activity volume (0-0.15): normalized by reasonable max
    volume = min((profile_views + applications) / 100.0, 1.0) * 0.15

    return min(resp_score + speed_score + interview_score + volume, 1.0)


def _compute_visibility(
    profile_views: int,
    saved_by_recruiters: int,
    search_appearance: int,
    profile_completeness: float,
) -> float:
    """Score candidate visibility 0-1."""
    # Profile completeness (0-0.40)
    completeness = min(profile_completeness / 100.0, 1.0) * 0.40

    # Recruiter interest (0-0.30)
    saved = min(saved_by_recruiters / 10.0, 1.0) * 0.30

    # Search appearances (0-0.20)
    search = min(search_appearance / 50.0, 1.0) * 0.20

    # Profile views (0-0.10)
    views = min(profile_views / 200.0, 1.0) * 0.10

    return min(completeness + saved + search + views, 1.0)


def _compute_credibility(
    verified_email: bool,
    verified_phone: bool,
    linkedin: bool,
    github_score: float,
    endorsements: int,
    connection_count: int,
) -> float:
    """Score candidate credibility 0-1."""
    score = 0.0

    # Verification (0-0.30)
    if verified_email:
        score += 0.15
    if verified_phone:
        score += 0.15

    # LinkedIn (0-0.20)
    if linkedin:
        score += 0.20

    # GitHub (0-0.25)
    if github_score >= 0:
        score += min(github_score / 100.0, 1.0) * 0.25

    # Endorsements (0-0.15)
    score += min(endorsements / 50.0, 1.0) * 0.15

    # Connections (0-0.10)
    score += min(connection_count / 500.0, 1.0) * 0.10

    return min(score, 1.0)


def _compute_availability(
    open_to_work: bool,
    notice_period: int,
    offer_acceptance: float,
) -> float:
    """Score candidate availability 0-1."""
    score = 0.0

    # Open to work (0-0.50)
    if open_to_work:
        score += 0.50

    # Notice period (0-0.30): shorter = more available
    if notice_period <= 15:
        score += 0.30
    elif notice_period <= 30:
        score += 0.25
    elif notice_period <= 60:
        score += 0.15
    elif notice_period <= 90:
        score += 0.10
    else:
        score += 0.05

    # Offer acceptance history (0-0.20)
    if offer_acceptance >= 0:
        score += min(offer_acceptance, 1.0) * 0.20
    else:
        score += 0.10  # neutral if no history

    return min(score, 1.0)


def _empty_signals() -> Dict[str, Any]:
    """Return empty/default signals when data is missing."""
    return {
        "engagement_score": 0.0,
        "visibility_score": 0.0,
        "credibility_score": 0.0,
        "availability_score": 0.0,
        "platform_activity_score": 0.0,
        "open_to_work": False,
        "recruiter_response_rate": 0.0,
        "notice_period_days": 30,
        "github_activity_score": -1,
        "profile_completeness": 0,
        "verified": False,
    }
