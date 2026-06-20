"""
AI Candidate Ranking Service.

Main orchestrator that takes a job description and a list of candidates,
computes multi-factor scores, ranks them, and produces explainable
output with strengths, weaknesses, and detailed breakdowns.
"""

import logging
import time
from typing import Dict, Any, List, Optional

from ..scores.skill_score import calculate_skill_score
from ..scores.experience_score import calculate_experience_score
from ..scores.education_score import calculate_education_score, get_education_summary
from ..scores.semantic_score import calculate_semantic_score
from ..scores.achievement_score import calculate_achievement_score, describe_achievements
from ..scores.platform_score import calculate_platform_score, describe_platform_signals
from ..utils.weights import RankingWeights, DEFAULT_WEIGHTS

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pydantic-style data models (using plain dicts for portability)
# ---------------------------------------------------------------------------

def _make_result(
    candidate_id: str,
    final_score: float,
    skill_score: float,
    experience_score: float,
    education_score: float,
    semantic_score: float,
    achievement_score: float,
    platform_score: float,
    rank: int,
    strengths: List[str],
    weaknesses: List[str],
    explanation: str,
    breakdown: Dict[str, float],
    skill_details: Dict[str, Any],
    education_summary: Dict[str, Any],
) -> Dict[str, Any]:
    """Build a single ranking result dict."""
    return {
        "candidate_id": candidate_id,
        "final_score": round(final_score, 2),
        "skill_score": round(skill_score, 2),
        "experience_score": round(experience_score, 2),
        "education_score": round(education_score, 2),
        "semantic_score": round(semantic_score, 2),
        "achievement_score": round(achievement_score, 2),
        "platform_score": round(platform_score, 2),
        "rank": rank,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "explanation": explanation,
        "breakdown": breakdown,
        "skill_details": skill_details,
        "education_summary": education_summary,
    }


# ---------------------------------------------------------------------------
# Main ranking function
# ---------------------------------------------------------------------------

def rank_candidates(
    job_description: Dict[str, Any],
    candidates: List[Dict[str, Any]],
    weights: Optional[RankingWeights] = None,
    job_embedding: Optional[List[float]] = None,
    top_n: int = 20,
) -> List[Dict[str, Any]]:
    """
    Rank candidates against a job description.

    Parameters
    ----------
    job_description : dict
        Parsed job description with keys: ``title``, ``skills``,
        ``experience``, ``education``, ``summary``.
    candidates : list[dict]
        List of candidate records from Part 1/2. Each must have at minimum:
        ``candidate_id`` (or ``id``), ``skills``, ``total_experience_years``
        (or ``experience_years``), ``education`` (optional), ``profile_summary``
        (or ``summary``), ``candidate_embedding`` (optional),
        ``leadership_score``, ``impact_score``, ``promotion_count``,
        ``career_growth_score``, ``seniority``.
    weights : RankingWeights, optional
        Scoring weights. Defaults to DEFAULT_WEIGHTS.
    job_embedding : list[float], optional
        384-dim job description embedding.
    top_n : int
        Number of top candidates to return.

    Returns
    -------
    list[dict]
        Ranked candidates sorted by final_score descending.
    """
    t0 = time.time()

    if weights is None:
        weights = DEFAULT_WEIGHTS
    weights.validate()

    # Extract job fields
    jd_skills = job_description.get("skills", [])
    jd_experience = job_description.get("experience", 0)
    jd_education = job_description.get("education", "")
    jd_seniority = job_description.get("seniority", "")
    jd_title = job_description.get("title", "")
    jd_summary = job_description.get("summary", "")

    # Combine job text for embedding if not provided
    if job_embedding is None:
        job_text = f"{jd_title} {jd_summary} {' '.join(jd_skills)}"
        # Caller should provide embedding; we use a placeholder
        logger.warning("No job_embedding provided. Semantic scores will be neutral.")

    results: List[Dict[str, Any]] = []

    for cand in candidates:
        result = _score_single_candidate(
            candidate=cand,
            jd_skills=jd_skills,
            jd_experience=jd_experience,
            jd_education=jd_education,
            jd_seniority=jd_seniority,
            job_embedding=job_embedding,
            weights=weights,
        )
        results.append(result)

    # Sort by final score descending, with tiebreakers
    results.sort(
        key=lambda x: (
            x["final_score"],
            x.get("breakdown", {}).get("semantic", 0),
            x.get("breakdown", {}).get("skill", 0),
            x.get("breakdown", {}).get("experience", 0),
        ),
        reverse=True,
    )

    # Assign ranks
    for i, r in enumerate(results, 1):
        r["rank"] = i

    elapsed = time.time() - t0
    logger.info("Ranked %d candidates in %.3fs", len(results), elapsed)

    return results[:top_n]


def _score_single_candidate(
    candidate: Dict[str, Any],
    jd_skills: List[str],
    jd_experience: int,
    jd_education: str,
    jd_seniority: str,
    job_embedding: Optional[List[float]],
    weights: RankingWeights,
) -> Dict[str, Any]:
    """Score a single candidate across all dimensions."""

    cand_id = candidate.get("candidate_id") or candidate.get("id", "UNKNOWN")

    # --- Normalise candidate fields ---
    cand_skills = candidate.get("skills", {})
    if isinstance(cand_skills, list):
        # Convert list of dicts to {name: score}
        cand_skills = {s.get("name", ""): 0.5 for s in cand_skills if s.get("name")}

    cand_years = candidate.get("total_experience_years") or candidate.get("experience_years", 0)
    cand_education = candidate.get("education", [])
    cand_seniority = candidate.get("seniority", "Mid")
    cand_embedding = candidate.get("candidate_embedding")
    leadership = candidate.get("leadership_score", 0.0)
    impact = candidate.get("impact_score", 0.0)
    promos = candidate.get("promotion_count", 0)
    growth = candidate.get("career_growth_score", 0.0)
    profile_text = candidate.get("profile_summary", "")

    # --- 1. Skill score ---
    skill_sc, skill_details = calculate_skill_score(
        candidate_skills=cand_skills,
        required_skills=jd_skills,
        preferred_skills=[],
    )

    # --- 2. Experience score ---
    exp_sc = calculate_experience_score(
        candidate_years=cand_years,
        required_years=jd_experience,
        candidate_seniority=cand_seniority,
        required_seniority=jd_seniority,
        leadership_score=leadership,
    )

    # --- 3. Education score ---
    edu_sc = calculate_education_score(
        candidate_education=cand_education,
        required_education=jd_education,
    )
    edu_summary = get_education_summary(cand_education)

    # --- 4. Semantic score ---
    sem_sc = calculate_semantic_score(
        job_embedding=job_embedding,
        candidate_embedding=cand_embedding,
    )

    # --- 5. Achievement score ---
    ach_sc = calculate_achievement_score(
        leadership_score=leadership,
        impact_score=impact,
        promotion_count=promos,
        career_growth_score=growth,
        profile_text=profile_text,
    )

    # --- 6. Platform activity score ---
    redrob = candidate.get("redrob_signals", {})
    plat_sc = calculate_platform_score(redrob)

    # --- 7. Final composite score ---
    final = (
        weights.skill * skill_sc
        + weights.experience * exp_sc
        + weights.semantic * sem_sc
        + weights.education * edu_sc
        + weights.achievement * ach_sc
        + weights.platform * plat_sc
    )

    # --- Apply Traps / Disqualifiers Penalties ---
    # 1. Non-tech title penalty
    # Use raw current title if merged, else fallback to profile summary title
    current_title = (candidate.get("current_title") or "").lower().strip()
    if not current_title:
        profile_summary = (candidate.get("profile_summary") or "").lower()
        current_title = profile_summary.split(" with ")[0].split(" at ")[0].strip()
    
    is_tech = False
    tech_keywords = ["engineer", "developer", "programmer", "scientist", "architect", "coding", "coder", "mts", "researcher"]
    for kw in tech_keywords:
        if kw in current_title:
            is_tech = True
            break
            
    # Also explicitly check for non-tech roles
    non_tech_keywords = ["marketing", "sales", "operations", "hr", "accountant", "civil", "mechanical", "graphic", "support", "writer", "scrum master", "agile coach", "recruiter", "talent acquisition", "analyst", "project manager", "product manager", "program manager"]
    is_explicit_non_tech = False
    for kw in non_tech_keywords:
        if kw in current_title:
            is_explicit_non_tech = True
            break
            
    # If title contains manager, verify it is a technical/engineering manager
    if "manager" in current_title:
        is_tech_manager = False
        tech_mgr_keywords = ["engineering", "technical", "development", "technology", "software"]
        for kw in tech_mgr_keywords:
            if kw in current_title:
                is_tech_manager = True
                break
        if not is_tech_manager:
            is_explicit_non_tech = True
            
    if not is_tech or is_explicit_non_tech:
        final = -100.0  # Disqualify non-tech roles completely

    # 2. Consulting firm penalty
    companies = candidate.get("companies", [])
    if companies:
        consulting_firms = {"tcs", "infosys", "wipro", "accenture", "cognizant", "capgemini", "tata consultancy", "wipro technologies"}
        only_consulting = True
        for comp in companies:
            comp_lower = comp.lower().strip()
            is_firm = False
            for firm in consulting_firms:
                if firm in comp_lower:
                    is_firm = True
                    break
            if not is_firm:
                only_consulting = False
                break
        if only_consulting:
            final -= 50.0  # Apply penalty for only working at consulting firms

    # 3. Honeypot check and disqualification
    if candidate.get("is_honeypot"):
        final -= 100.0  # Disqualify honeypot profiles completely

    final = round(max(0, min(100, final)), 2)

    # --- 8. Generate strengths and weaknesses ---
    strengths, weaknesses = _generate_strengths_weaknesses(
        skill_details=skill_details,
        skill_score=skill_sc,
        experience_score=exp_sc,
        experience_years=cand_years,
        required_experience=jd_experience,
        education_score=edu_sc,
        education_summary=edu_summary,
        semantic_score=sem_sc,
        achievement_score=ach_sc,
        leadership=leadership,
        impact=impact,
        promotion_count=promos,
        seniority=cand_seniority,
        required_seniority=jd_seniority,
        platform_score=plat_sc,
        redrob_signals=redrob,
    )

    # --- 8. Generate explanation ---
    explanation = _generate_explanation(
        candidate_id=cand_id,
        skill_details=skill_details,
        experience_years=cand_years,
        required_experience=jd_experience,
        semantic_score=sem_sc,
        education_summary=edu_summary,
        promotion_count=promos,
        leadership=leadership,
        seniority=cand_seniority,
        platform_score=plat_sc,
        redrob_signals=redrob,
    )

    # --- 9. Breakdown for visualization ---
    breakdown = {
        "skill": round(skill_sc, 2),
        "experience": round(exp_sc, 2),
        "education": round(edu_sc, 2),
        "semantic": round(sem_sc, 2),
        "achievement": round(ach_sc, 2),
        "platform": round(plat_sc, 2),
    }

    return _make_result(
        candidate_id=cand_id,
        final_score=final,
        skill_score=skill_sc,
        experience_score=exp_sc,
        education_score=edu_sc,
        semantic_score=sem_sc,
        achievement_score=ach_sc,
        platform_score=plat_sc,
        rank=0,  # assigned after sorting
        strengths=strengths,
        weaknesses=weaknesses,
        explanation=explanation,
        breakdown=breakdown,
        skill_details=skill_details,
        education_summary=edu_summary,
    )


# ---------------------------------------------------------------------------
# Strengths / Weaknesses generation
# ---------------------------------------------------------------------------

def _generate_strengths_weaknesses(
    skill_details: Dict[str, Any],
    skill_score: float,
    experience_score: float,
    experience_years: float,
    required_experience: int,
    education_score: float,
    education_summary: Dict[str, Any],
    semantic_score: float,
    achievement_score: float,
    leadership: float,
    impact: float,
    promotion_count: int,
    seniority: str,
    required_seniority: str,
    platform_score: float = 0.0,
    redrob_signals: Dict[str, Any] = None,
) -> tuple:
    """Generate lists of strengths and weaknesses."""

    strengths: List[str] = []
    weaknesses: List[str] = []

    # --- Skills ---
    matched_req = skill_details.get("matched_required", [])
    missing_req = skill_details.get("missing_required", [])
    related = skill_details.get("related_matches", [])
    total_req = skill_details.get("required_count", 0)

    if total_req > 0 and not missing_req:
        strengths.append(f"Matches all {len(matched_req)}/{total_req} required skills")
    elif matched_req:
        strengths.append(f"Matches {len(matched_req)}/{total_req} required skills")

    if related:
        strengths.append(f"Has related skills: {', '.join(r.split(' (')[0] for r in related[:3])}")

    if missing_req:
        weaknesses.append(f"Missing required skills: {', '.join(missing_req[:3])}")

    # --- Experience ---
    if experience_score >= 85:
        if required_experience > 0 and experience_years > required_experience:
            strengths.append(f"Exceeds experience requirement ({experience_years:.1f}y vs {required_experience}y required)")
        else:
            strengths.append(f"Meets experience requirement ({experience_years:.1f} years)")
    elif experience_score >= 60:
        strengths.append(f"Close to experience requirement ({experience_years:.1f} years)")
    else:
        weaknesses.append(f"Below experience requirement ({experience_years:.1f}y vs {required_experience}y required)")

    # --- Education ---
    if education_score >= 90:
        strengths.append(f"Strong educational background ({education_summary.get('highest_degree', '?')})")
    elif education_score >= 80:
        strengths.append(f"Good educational background ({education_summary.get('highest_degree', '?')})")
    elif education_score < 60:
        weaknesses.append(f"Education below requirement ({education_summary.get('highest_degree', 'unknown')})")

    # --- Semantic ---
    if semantic_score >= 80:
        strengths.append("Excellent semantic match with job description")
    elif semantic_score >= 65:
        strengths.append("Strong semantic alignment with the role")

    # --- Achievements ---
    if leadership >= 0.6:
        strengths.append("Strong leadership experience")
    elif leadership < 0.2:
        weaknesses.append("Limited leadership evidence")

    if impact >= 0.5:
        strengths.append("Track record of measurable impact")
    elif impact < 0.2:
        weaknesses.append("Limited measurable impact in profile")

    if promotion_count >= 3:
        strengths.append(f"Fast career progression ({promotion_count} promotions)")
    elif promotion_count >= 1:
        strengths.append(f"Career growth demonstrated ({promotion_count} promotion{'s' if promotion_count > 1 else ''})")

    # --- Seniority ---
    if required_seniority:
        from ..utils.weights import SENIORITY_LEVELS
        c_level = SENIORITY_LEVELS.get(seniority.lower(), 0)
        r_level = SENIORITY_LEVELS.get(required_seniority.lower(), 0)
        if c_level > 0 and r_level > 0:
            if c_level == r_level:
                strengths.append(f"Exact seniority match ({seniority})")
            elif c_level > r_level:
                strengths.append(f"Seniority above requirement ({seniority} vs {required_seniority})")
            elif c_level == r_level - 1:
                weaknesses.append(f"Slightly below required seniority ({seniority} vs {required_seniority})")
            else:
                weaknesses.append(f"Below required seniority ({seniority} vs {required_seniority})")

    # --- Platform activity ---
    if redrob_signals:
        if redrob_signals.get("open_to_work"):
            strengths.append("Actively open to work")
        response_rate = redrob_signals.get("recruiter_response_rate", 0)
        if response_rate >= 0.7:
            strengths.append(f"Highly responsive to recruiters ({response_rate:.0%})")
        elif response_rate < 0.3 and response_rate > 0:
            weaknesses.append(f"Low recruiter response rate ({response_rate:.0%})")
        github = redrob_signals.get("github_activity_score", -1)
        if github >= 70:
            strengths.append(f"Strong GitHub activity (score {github:.0f})")
        notice = redrob_signals.get("notice_period_days", 30)
        if notice <= 15:
            strengths.append(f"Quick availability ({notice}d notice)")
        elif notice > 60:
            weaknesses.append(f"Long notice period ({notice}d)")
    if platform_score >= 75:
        strengths.append(f"Strong platform engagement (score {platform_score:.0f})")
    elif platform_score < 40:
        weaknesses.append(f"Low platform activity (score {platform_score:.0f})")

    # Fallback
    if not strengths:
        strengths.append("Profile has relevant background")
    if not weaknesses:
        weaknesses.append("No significant weaknesses identified")

    return strengths, weaknesses


# ---------------------------------------------------------------------------
# Explanation generation
# ---------------------------------------------------------------------------

def _generate_explanation(
    candidate_id: str,
    skill_details: Dict[str, Any],
    experience_years: float,
    required_experience: int,
    semantic_score: float,
    education_summary: Dict[str, Any],
    promotion_count: int,
    leadership: float,
    seniority: str,
    platform_score: float = 0.0,
    redrob_signals: Dict[str, Any] = None,
) -> str:
    """Generate a natural-language explanation for the ranking."""
    parts: List[str] = []

    # Skills
    matched = skill_details.get("matched_required", [])
    missing = skill_details.get("missing_required", [])
    total = skill_details.get("required_count", 0)
    related = skill_details.get("related_matches", [])

    if total > 0:
        if not missing:
            parts.append(f"Candidate matches all {len(matched)} of {total} required skills")
        else:
            parts.append(f"Candidate matches {len(matched)} of {total} required skills")
        if missing:
            parts.append(f"but is missing {', '.join(missing[:2])}")
        if related:
            parts.append(f"and has related skills ({', '.join(r.split(' (')[0] for r in related[:2])})")

    # Experience
    if required_experience > 0:
        if experience_years >= required_experience:
            parts.append(f"has {experience_years:.1f} years of experience exceeding the {required_experience}-year requirement")
        else:
            parts.append(f"has {experience_years:.1f} years of experience (requirement: {required_experience} years)")
    else:
        parts.append(f"has {experience_years:.1f} years of experience")

    # Semantic
    if semantic_score >= 75:
        parts.append(f"shows strong semantic alignment with the role ({semantic_score:.0f}%)")
    elif semantic_score >= 55:
        parts.append(f"shows good alignment with the role ({semantic_score:.0f}%)")

    # Education
    degree = education_summary.get("highest_degree", "")
    if degree and degree != "unknown":
        parts.append(f"holds a {degree} degree")

    # Leadership / achievements
    if leadership >= 0.5:
        parts.append("and possesses strong leadership experience")
    if promotion_count >= 2:
        parts.append(f"with {promotion_count} career promotions")

    # Platform activity
    if redrob_signals:
        if redrob_signals.get("open_to_work"):
            parts.append("actively open to work")
        response_rate = redrob_signals.get("recruiter_response_rate", 0)
        if response_rate >= 0.7:
            parts.append(f"with high recruiter response rate ({response_rate:.0%})")
        notice = redrob_signals.get("notice_period_days", 30)
        if notice <= 15:
            parts.append(f"available to start in {notice} days")
        elif notice > 60:
            parts.append(f"requires {notice}-day notice period")

    if not parts:
        parts.append("Profile has relevant background for the role")

    # Capitalise first letter
    result = ", ".join(parts)
    return result[0].upper() + result[1:] if result else ""


# ---------------------------------------------------------------------------
# Convenience: rank from raw Part 1 JSONL
# ---------------------------------------------------------------------------

def rank_from_file(
    candidates_path: str,
    job_description: Dict[str, Any],
    job_embedding: Optional[List[float]] = None,
    weights: Optional[RankingWeights] = None,
    top_n: int = 20,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Load candidates from a JSONL file and rank them.

    Parameters
    ----------
    candidates_path : str
        Path to processed_candidates.jsonl.
    job_description : dict
        Parsed job description.
    job_embedding : list[float], optional
        Job description embedding.
    weights : RankingWeights, optional
        Custom weights.
    top_n : int
        Number of top results to return.
    limit : int, optional
        Maximum number of candidates to load.

    Returns
    -------
    list[dict]
        Ranked candidates.
    """
    import json

    candidates = []
    with open(candidates_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if not line.strip():
                continue
            candidates.append(json.loads(line))
            if limit and i + 1 >= limit:
                break

    logger.info("Loaded %d candidates from %s", len(candidates), candidates_path)

    return rank_candidates(
        job_description=job_description,
        candidates=candidates,
        weights=weights,
        job_embedding=job_embedding,
        top_n=top_n,
    )
