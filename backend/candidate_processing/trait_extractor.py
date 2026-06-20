"""
Trait extraction: leadership, impact, domain expertise, and seniority.

Infers hidden signals from career descriptions, skills, and titles.
"""

from typing import Dict, Any, List

from .config import (
    LEADERSHIP_KEYWORDS,
    IMPACT_KEYWORDS,
    DOMAIN_KEYWORDS,
    JUNIOR_MAX_YEARS,
    MID_MAX_YEARS,
    SENIOR_MAX_YEARS,
    LEAD_MAX_YEARS,
)
from .utils import safe_float, clamp, count_keyword_hits


def _leadership_score(
    career_history: List[Dict[str, Any]],
    current_title: str,
) -> float:
    """Score leadership evidence from descriptions and title."""
    combined = current_title.lower()
    for entry in career_history:
        desc = entry.get("description") or ""
        combined += " " + desc.lower()

    hits = count_keyword_hits(combined, LEADERSHIP_KEYWORDS)
    # normalize: 5+ hits -> 1.0
    return round(clamp(hits / 5.0), 4)


def _impact_score(career_history: List[Dict[str, Any]]) -> float:
    """Score evidence of measurable impact from career descriptions."""
    combined = ""
    for entry in career_history:
        combined += " " + (entry.get("description") or "").lower()

    hits = count_keyword_hits(combined, IMPACT_KEYWORDS)
    # look for numeric metrics (percentages, dollar amounts)
    import re
    metric_pattern = re.compile(r"\d+[%$kKmM]|improved|reduced|increased|saved|cut|boosted|accelerated|shipped|launched|deployed|scaled|built.*system")
    metric_hits = len(metric_pattern.findall(combined))

    total = hits + metric_hits
    return round(clamp(total / 8.0), 4)


def _domain_expertise(
    skills: Dict[str, float],
    career_history: List[Dict[str, Any]],
    summary: str,
) -> Dict[str, float]:
    """
    Build a ``{domain: score}`` mapping.

    Combines skill evidence with keyword matches in career descriptions
    and summary text.
    """
    combined_text = summary.lower()
    for entry in career_history:
        combined_text += " " + (entry.get("description") or "").lower()

    skill_names = list(skills.keys())
    all_text = combined_text + " " + " ".join(skill_names)

    domains: Dict[str, float] = {}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        hits = count_keyword_hits(all_text, keywords)
        # Also check if any of the candidate's skills match the domain keywords
        skill_hits = sum(1 for sk in skill_names if sk in keywords)
        score = clamp((hits * 0.3 + skill_hits * 0.7) / 4.0)
        if score > 0.05:
            domains[domain] = round(score, 4)

    # sort descending
    return dict(sorted(domains.items(), key=lambda kv: kv[1], reverse=True))


def _classify_seniority(
    total_years: float,
    career_growth_score: float,
    leadership: float,
    promotion_count: int,
    has_phd: bool,
) -> str:
    """
    Classify overall seniority level.

    Primarily driven by total years of experience with adjustments for
    career growth signals, leadership, and promotions.

    Heuristic thresholds:
    - < 2 years  -> Junior
    - 2-5 years  -> Mid
    - 5-10 years -> Senior
    - 10-15 years -> Lead
    - 15+ years  -> Principal
    """
    # Base score from experience
    exp_score = clamp(total_years / 15.0)

    # Bonus signals
    bonus = (
        career_growth_score * 0.20
        + leadership * 0.10
        + clamp(promotion_count / 3.0) * 0.10
        + (0.05 if has_phd else 0.0)
    )

    composite = exp_score + bonus

    if composite >= 0.85:
        return "Principal"
    if composite >= 0.70:
        return "Lead"
    if composite >= 0.45:
        return "Senior"
    if composite >= 0.25:
        return "Mid"
    return "Junior"


class TraitExtractor:
    """Extract leadership, impact, domain expertise, and seniority."""

    def extract(
        self,
        profile: Dict[str, Any],
        career_history: List[Dict[str, Any]],
        skills: Dict[str, float],
        education_info: Dict[str, Any],
        career_info: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Return a dict of extracted traits.

        Parameters
        ----------
        profile : dict
            Candidate profile.
        career_history : list[dict]
            Raw career history.
        skills : dict
            Normalised skill scores.
        education_info : dict
            Output of EducationAnalyzer.analyze().
        career_info : dict
            Output of CareerAnalyzer.analyze().

        Returns
        -------
        dict with ``leadership_score``, ``impact_score``,
        ``domain_expertise``, ``seniority``.
        """
        current_title = profile.get("current_title") or ""
        summary = profile.get("summary") or ""

        lead = _leadership_score(career_history, current_title)
        impact = _impact_score(career_history)
        domains = _domain_expertise(skills, career_history, summary)

        seniority = _classify_seniority(
            total_years=career_info.get("total_experience_years", 0.0),
            career_growth_score=career_info.get("career_growth_score", 0.0),
            leadership=lead,
            promotion_count=career_info.get("promotion_count", 0),
            has_phd=education_info.get("has_phd", False),
        )

        return {
            "leadership_score": lead,
            "impact_score": impact,
            "domain_expertise": domains,
            "seniority": seniority,
        }
