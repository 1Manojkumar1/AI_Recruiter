"""
Candidate Comparison Engine

Explains why one candidate ranks higher than another by comparing
their profiles across all scoring dimensions.
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


def compare_candidates(
    candidate_a: Dict[str, Any],
    candidate_b: Dict[str, Any],
    scores_a: Dict[str, float],
    scores_b: Dict[str, float],
    job_description: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Compare two candidates and explain ranking differences.

    Parameters
    ----------
    candidate_a : dict
        Higher-ranked candidate profile.
    candidate_b : dict
        Lower-ranked candidate profile.
    scores_a : dict
        Scores for candidate A (skill_score, experience_score, etc.).
    scores_b : dict
        Scores for candidate B (skill_score, experience_score, etc.).
    job_description : dict, optional
        Parsed JD for context.

    Returns
    -------
    dict with keys: candidate_A_advantage, candidate_B_advantage, final_reason.
    """
    cand_a_id = candidate_a.get("candidate_id") or candidate_a.get("id", "A")
    cand_b_id = candidate_b.get("candidate_id") or candidate_b.get("id", "B")

    advantages_a: List[str] = []
    advantages_b: List[str] = []

    # --- Compare each dimension ---
    dimensions = [
        ("skill_score", "Skill Match"),
        ("experience_score", "Experience"),
        ("education_score", "Education"),
        ("semantic_score", "Semantic Alignment"),
        ("achievement_score", "Achievements"),
    ]

    for score_key, dim_name in dimensions:
        sa = scores_a.get(score_key, 0)
        sb = scores_b.get(score_key, 0)
        diff = sa - sb

        if abs(diff) < 2:
            continue  # Negligible difference

        if diff > 0:
            advantages_a.append(f"{dim_name}: {sa:.0f} vs {sb:.0f} (+{diff:.0f} points)")
        else:
            advantages_b.append(f"{dim_name}: {sb:.0f} vs {sa:.0f} (+{abs(diff):.0f} points)")

    # --- Compare specific attributes ---
    _compare_experience(candidate_a, candidate_b, advantages_a, advantages_b)
    _compare_skills(candidate_a, candidate_b, job_description, advantages_a, advantages_b)
    _compare_seniority(candidate_a, candidate_b, advantages_a, advantages_b)
    _compare_achievements(candidate_a, candidate_b, advantages_a, advantages_b)

    # --- Final reason ---
    final_score_a = scores_a.get("final_score", 0)
    final_score_b = scores_b.get("final_score", 0)
    final_reason = _generate_final_reason(
        cand_a_id=cand_a_id,
        cand_b_id=cand_b_id,
        final_score_a=final_score_a,
        final_score_b=final_score_b,
        advantages_a=advantages_a,
        advantages_b=advantages_b,
    )

    if not advantages_a:
        advantages_a.append("No significant advantages identified")
    if not advantages_b:
        advantages_b.append("No significant advantages identified")

    return {
        "candidate_A_id": cand_a_id,
        "candidate_B_id": cand_b_id,
        "candidate_A_advantage": advantages_a,
        "candidate_B_advantage": advantages_b,
        "final_reason": final_reason,
    }


def _compare_experience(
    cand_a: Dict[str, Any],
    cand_b: Dict[str, Any],
    adv_a: List[str],
    adv_b: List[str],
) -> None:
    """Compare experience between two candidates."""
    years_a = cand_a.get("total_experience_years", 0)
    years_b = cand_b.get("total_experience_years", 0)

    if abs(years_a - years_b) >= 1.0:
        if years_a > years_b:
            adv_a.append(f"More experience ({years_a:.1f}y vs {years_b:.1f}y)")
        else:
            adv_b.append(f"More experience ({years_b:.1f}y vs {years_a:.1f}y)")


def _compare_skills(
    cand_a: Dict[str, Any],
    cand_b: Dict[str, Any],
    job_description: Optional[Dict[str, Any]],
    adv_a: List[str],
    adv_b: List[str],
) -> None:
    """Compare skill coverage between two candidates."""
    if not job_description:
        return

    jd_skills = job_description.get("skills", job_description.get("required_skills", []))
    if not jd_skills:
        return

    skills_a = cand_a.get("skills", {})
    skills_b = cand_b.get("skills", {})
    if isinstance(skills_a, list):
        skills_a = {s.get("name", ""): 0.5 for s in skills_a}
    if isinstance(skills_b, list):
        skills_b = {s.get("name", ""): 0.5 for s in skills_b}

    names_a = {k.lower() for k in skills_a.keys()}
    names_b = {k.lower() for k in skills_b.keys()}

    matched_a = sum(1 for s in jd_skills if s.lower() in names_a)
    matched_b = sum(1 for s in jd_skills if s.lower() in names_b)

    if matched_a != matched_b:
        if matched_a > matched_b:
            adv_a.append(f"Covers more required skills ({matched_a}/{len(jd_skills)} vs {matched_b}/{len(jd_skills)})")
        else:
            adv_b.append(f"Covers more required skills ({matched_b}/{len(jd_skills)} vs {matched_a}/{len(jd_skills)})")


def _compare_seniority(
    cand_a: Dict[str, Any],
    cand_b: Dict[str, Any],
    adv_a: List[str],
    adv_b: List[str],
) -> None:
    """Compare seniority levels."""
    from ..part3.utils.weights import SENIORITY_LEVELS

    sen_a = cand_a.get("seniority", "Mid")
    sen_b = cand_b.get("seniority", "Mid")
    level_a = SENIORITY_LEVELS.get(sen_a.lower(), 0)
    level_b = SENIORITY_LEVELS.get(sen_b.lower(), 0)

    if level_a != level_b:
        if level_a > level_b:
            adv_a.append(f"Higher seniority ({sen_a} vs {sen_b})")
        else:
            adv_b.append(f"Higher seniority ({sen_b} vs {sen_a})")


def _compare_achievements(
    cand_a: Dict[str, Any],
    cand_b: Dict[str, Any],
    adv_a: List[str],
    adv_b: List[str],
) -> None:
    """Compare leadership and impact achievements."""
    lead_a = cand_a.get("leadership_score", 0)
    lead_b = cand_b.get("leadership_score", 0)
    if abs(lead_a - lead_b) >= 0.3:
        if lead_a > lead_b:
            adv_a.append(f"Stronger leadership evidence ({lead_a:.2f} vs {lead_b:.2f})")
        else:
            adv_b.append(f"Stronger leadership evidence ({lead_b:.2f} vs {lead_a:.2f})")

    impact_a = cand_a.get("impact_score", 0)
    impact_b = cand_b.get("impact_score", 0)
    if abs(impact_a - impact_b) >= 0.3:
        if impact_a > impact_b:
            adv_a.append(f"Stronger impact metrics ({impact_a:.2f} vs {impact_b:.2f})")
        else:
            adv_b.append(f"Stronger impact metrics ({impact_b:.2f} vs {impact_a:.2f})")

    promos_a = cand_a.get("promotion_count", 0)
    promos_b = cand_b.get("promotion_count", 0)
    if promos_a != promos_b:
        if promos_a > promos_b:
            adv_a.append(f"More career progression ({promos_a} promotions vs {promos_b})")
        else:
            adv_b.append(f"More career progression ({promos_b} promotions vs {promos_a})")


def _generate_final_reason(
    cand_a_id: str,
    cand_b_id: str,
    final_score_a: float,
    final_score_b: float,
    advantages_a: List[str],
    advantages_b: List[str],
) -> str:
    """Generate a final summary reason for the ranking difference."""
    diff = final_score_a - final_score_b

    if diff >= 20:
        strength = "significantly"
    elif diff >= 10:
        strength = "moderately"
    elif diff >= 5:
        strength = "slightly"
    else:
        strength = "marginally"

    parts = [f"Candidate {cand_a_id} ranks {strength} higher ({final_score_a:.0f} vs {final_score_b:.0f})"]

    # Find the biggest advantage
    if advantages_a:
        biggest = advantages_a[0]
        parts.append(f"primarily due to {biggest.lower()}")

    return ". ".join(parts) + "."
