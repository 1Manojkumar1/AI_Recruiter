"""
LLM Explanation Engine

Generates human-readable explanations for candidate rankings using
template-based natural language generation. No external LLM API required.
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Thresholds for classification
# ---------------------------------------------------------------------------
HIGH_SCORE = 80
MEDIUM_SCORE = 60
LOW_SCORE = 40


def generate_explanation(
    job_description: Dict[str, Any],
    candidate_profile: Dict[str, Any],
    scores: Dict[str, float],
) -> Dict[str, Any]:
    """
    Generate a full explanation for a candidate's ranking.

    Parameters
    ----------
    job_description : dict
        Parsed JD with keys: title, skills, experience, education, summary, seniority.
    candidate_profile : dict
        Candidate record from Part 1 processing.
    scores : dict
        Scoring breakdown with keys: skill_score, experience_score, education_score,
        semantic_score, achievement_score, final_score.

    Returns
    -------
    dict with keys: strengths, weaknesses, summary, recommendation.
    """
    skill_score = scores.get("skill_score", 0)
    experience_score = scores.get("experience_score", 0)
    education_score = scores.get("education_score", 0)
    semantic_score = scores.get("semantic_score", 0)
    achievement_score = scores.get("achievement_score", 0)
    final_score = scores.get("final_score", 0)

    jd_skills = job_description.get("skills", job_description.get("required_skills", []))
    jd_experience = job_description.get("experience", 0)
    jd_seniority = job_description.get("seniority", "")
    jd_title = job_description.get("title", "")

    cand_skills = candidate_profile.get("skills", {})
    if isinstance(cand_skills, list):
        cand_skills = {s.get("name", ""): 0.5 for s in cand_skills if s.get("name")}
    cand_years = candidate_profile.get("total_experience_years", 0)
    cand_seniority = candidate_profile.get("seniority", "Mid")
    cand_education = candidate_profile.get("education", [])
    leadership = candidate_profile.get("leadership_score", 0)
    impact = candidate_profile.get("impact_score", 0)
    promos = candidate_profile.get("promotion_count", 0)
    growth = candidate_profile.get("career_growth_score", 0)

    strengths = _generate_strengths(
        skill_score=skill_score,
        experience_score=experience_score,
        education_score=education_score,
        semantic_score=semantic_score,
        achievement_score=achievement_score,
        jd_skills=jd_skills,
        cand_skills=cand_skills,
        cand_years=cand_years,
        jd_experience=jd_experience,
        cand_seniority=cand_seniority,
        jd_seniority=jd_seniority,
        leadership=leadership,
        impact=impact,
        promos=promos,
        growth=growth,
    )

    weaknesses = _generate_weaknesses(
        skill_score=skill_score,
        experience_score=experience_score,
        education_score=education_score,
        semantic_score=semantic_score,
        achievement_score=achievement_score,
        jd_skills=jd_skills,
        cand_skills=cand_skills,
        cand_years=cand_years,
        jd_experience=jd_experience,
        cand_seniority=cand_seniority,
        jd_seniority=jd_seniority,
        leadership=leadership,
        impact=impact,
    )

    summary = _generate_summary(
        jd_title=jd_title,
        final_score=final_score,
        skill_score=skill_score,
        experience_score=experience_score,
        cand_years=cand_years,
        cand_seniority=cand_seniority,
        strengths=strengths,
        weaknesses=weaknesses,
    )

    recommendation = _generate_recommendation(final_score)

    return {
        "strengths": strengths,
        "weaknesses": weaknesses,
        "summary": summary,
        "recommendation": recommendation,
    }


def generate_short_explanation(
    scores: Dict[str, float],
    jd_title: str = "",
    candidate_seniority: str = "",
    matched_skills: Optional[List[str]] = None,
) -> str:
    """
    Generate a one-sentence explanation.

    Parameters
    ----------
    scores : dict
        Must contain 'final_score' and optionally 'skill_score'.
    jd_title : str
        Job title for context.
    candidate_seniority : str
        Candidate seniority level.
    matched_skills : list[str], optional
        Skills that matched the JD.

    Returns
    -------
    str
        One-sentence explanation.
    """
    final = scores.get("final_score", 0)
    skill = scores.get("skill_score", 0)
    matched = matched_skills or []

    if final >= HIGH_SCORE:
        quality = "strong"
    elif final >= MEDIUM_SCORE:
        quality = "good"
    elif final >= LOW_SCORE:
        quality = "moderate"
    else:
        quality = "limited"

    parts = [f"{candidate_seniority} candidate" if candidate_seniority else "Candidate"]
    parts.append(f"is a {quality} fit")

    if jd_title:
        parts.append(f"for {jd_title}")

    if matched:
        top_skills = matched[:3]
        parts.append(f"because of {', '.join(top_skills)} experience")

    parts.append(f"(score: {final:.0f}/100)")

    return " ".join(parts) + "."


# ---------------------------------------------------------------------------
# Strengths generation
# ---------------------------------------------------------------------------

def _generate_strengths(
    skill_score: float,
    experience_score: float,
    education_score: float,
    semantic_score: float,
    achievement_score: float,
    jd_skills: List[str],
    cand_skills: Dict[str, float],
    cand_years: float,
    jd_experience: int,
    cand_seniority: str,
    jd_seniority: str,
    leadership: float,
    impact: float,
    promos: int,
    growth: float,
) -> List[str]:
    """Generate list of candidate strengths."""
    strengths: List[str] = []

    # Skill strengths
    matched = [s for s in jd_skills if s.lower() in {k.lower() for k in cand_skills}]
    if jd_skills:
        match_ratio = len(matched) / len(jd_skills) if jd_skills else 0
        if match_ratio >= 0.8:
            strengths.append(f"Excellent skill alignment: matches {len(matched)}/{len(jd_skills)} required skills ({', '.join(matched[:4])})")
        elif match_ratio >= 0.5:
            strengths.append(f"Good skill coverage: matches {len(matched)}/{len(jd_skills)} required skills ({', '.join(matched[:3])})")
        elif matched:
            strengths.append(f"Has {len(matched)} relevant skill(s): {', '.join(matched[:3])}")

    # Experience strengths
    if experience_score >= HIGH_SCORE:
        if jd_experience > 0 and cand_years > jd_experience:
            strengths.append(f"Exceeds experience requirement with {cand_years:.1f} years (need {jd_experience})")
        else:
            strengths.append(f"Strong experience level with {cand_years:.1f} years in the field")
    elif experience_score >= MEDIUM_SCORE:
        strengths.append(f"Adequate experience ({cand_years:.1f} years)")

    # Education strengths
    if education_score >= HIGH_SCORE:
        degree = _get_highest_degree([])
        strengths.append(f"Strong educational background ({degree})")
    elif education_score >= MEDIUM_SCORE:
        strengths.append("Meets educational requirements")

    # Semantic match
    if semantic_score >= HIGH_SCORE:
        strengths.append("Profile strongly aligns with job description context")
    elif semantic_score >= MEDIUM_SCORE:
        strengths.append("Good overall profile-job alignment")

    # Achievements
    if leadership >= 0.6:
        strengths.append("Demonstrated leadership experience")
    if impact >= 0.5:
        strengths.append("Track record of measurable impact and results")
    if promos >= 3:
        strengths.append(f"Fast career progression with {promos} promotions")
    elif promos >= 1:
        strengths.append(f"Career growth evidenced by {promos} promotion(s)")
    if growth >= 0.6:
        strengths.append("Strong career growth trajectory")

    # Seniority match
    if jd_seniority:
        from ..part3.utils.weights import SENIORITY_LEVELS
        c_level = SENIORITY_LEVELS.get(cand_seniority.lower(), 0)
        r_level = SENIORITY_LEVELS.get(jd_seniority.lower(), 0)
        if c_level > 0 and r_level > 0 and c_level >= r_level:
            strengths.append(f"Seniority level ({cand_seniority}) meets or exceeds requirement ({jd_seniority})")

    if not strengths:
        strengths.append("Profile has relevant background for the role")

    return strengths


# ---------------------------------------------------------------------------
# Weaknesses generation
# ---------------------------------------------------------------------------

def _generate_weaknesses(
    skill_score: float,
    experience_score: float,
    education_score: float,
    semantic_score: float,
    achievement_score: float,
    jd_skills: List[str],
    cand_skills: Dict[str, float],
    cand_years: float,
    jd_experience: int,
    cand_seniority: str,
    jd_seniority: str,
    leadership: float,
    impact: float,
) -> List[str]:
    """Generate list of candidate weaknesses."""
    weaknesses: List[str] = []

    # Skill gaps
    matched = [s for s in jd_skills if s.lower() in {k.lower() for k in cand_skills}]
    missing = [s for s in jd_skills if s.lower() not in {k.lower() for k in cand_skills}]
    if missing and jd_skills:
        weaknesses.append(f"Missing required skills: {', '.join(missing[:4])}")
    if skill_score < LOW_SCORE and jd_skills:
        weaknesses.append(f"Low skill match score ({skill_score:.0f}/100)")

    # Experience gaps
    if experience_score < MEDIUM_SCORE:
        if jd_experience > 0 and cand_years < jd_experience * 0.7:
            weaknesses.append(f"Significantly below experience requirement ({cand_years:.1f}y vs {jd_experience}y needed)")
        elif jd_experience > 0 and cand_years < jd_experience:
            weaknesses.append(f"Below experience requirement ({cand_years:.1f}y vs {jd_experience}y needed)")

    # Education gaps
    if education_score < MEDIUM_SCORE:
        weaknesses.append("Education background may not meet requirements")

    # Seniority mismatch
    if jd_seniority:
        from ..part3.utils.weights import SENIORITY_LEVELS
        c_level = SENIORITY_LEVELS.get(cand_seniority.lower(), 0)
        r_level = SENIORITY_LEVELS.get(jd_seniority.lower(), 0)
        if c_level > 0 and r_level > 0 and c_level < r_level - 1:
            weaknesses.append(f"Seniority ({cand_seniority}) below requirement ({jd_seniority})")
        elif c_level > 0 and r_level > 0 and c_level == r_level - 1:
            weaknesses.append(f"Slightly below required seniority ({cand_seniority} vs {jd_seniority})")

    # Leadership/impact
    if leadership < 0.2:
        weaknesses.append("Limited leadership evidence in profile")
    if impact < 0.2:
        weaknesses.append("Limited measurable impact demonstrated")

    # Semantic
    if semantic_score < LOW_SCORE:
        weaknesses.append("Profile has low contextual alignment with the job description")

    if not weaknesses:
        weaknesses.append("No significant weaknesses identified")

    return weaknesses


# ---------------------------------------------------------------------------
# Summary generation
# ---------------------------------------------------------------------------

def _generate_summary(
    jd_title: str,
    final_score: float,
    skill_score: float,
    experience_score: float,
    cand_years: float,
    cand_seniority: str,
    strengths: List[str],
    weaknesses: List[str],
) -> str:
    """Generate a natural-language summary paragraph."""
    if final_score >= HIGH_SCORE:
        opener = f"This {cand_seniority} candidate is an excellent fit"
    elif final_score >= MEDIUM_SCORE:
        opener = f"This {cand_seniority} candidate is a good fit"
    elif final_score >= LOW_SCORE:
        opener = f"This {cand_seniority} candidate is a moderate fit"
    else:
        opener = f"This {cand_seniority} candidate has limited alignment"

    if jd_title:
        opener += f" for the {jd_title} role"

    opener += f" with an overall score of {final_score:.0f}/100"

    details = []
    if cand_years > 0:
        details.append(f"bringing {cand_years:.1f} years of experience")
    if skill_score >= HIGH_SCORE:
        details.append("with strong skill coverage")
    elif skill_score >= MEDIUM_SCORE:
        details.append("with adequate skill coverage")
    elif skill_score > 0:
        details.append("but with notable skill gaps")

    if details:
        opener += ", " + ", ".join(details)

    # Add top strength
    if strengths and strengths[0] != "Profile has relevant background for the role":
        opener += f". {strengths[0]}"

    # Add main concern if any
    real_weaknesses = [w for w in weaknesses if w != "No significant weaknesses identified"]
    if real_weaknesses:
        opener += f". {real_weaknesses[0]}"

    opener += "."

    return opener


# ---------------------------------------------------------------------------
# Recommendation
# ---------------------------------------------------------------------------

def _generate_recommendation(final_score: float) -> str:
    """Generate a hiring recommendation based on score."""
    if final_score >= HIGH_SCORE:
        return "Highly Recommended"
    elif final_score >= MEDIUM_SCORE:
        return "Recommended"
    elif final_score >= LOW_SCORE:
        return "Consider with Reservations"
    else:
        return "Not Recommended"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_highest_degree(education: List[Any]) -> str:
    """Extract highest degree from education list."""
    hierarchy = ["phd", "doctorate", "masters", "mba", "m.s.", "m.sc.", "m.tech",
                 "bachelors", "b.e.", "b.tech", "b.sc.", "associate", "diploma"]
    for level in hierarchy:
        for edu in education:
            if isinstance(edu, dict):
                deg = str(edu.get("degree", "")).lower()
                if level in deg:
                    return edu.get("degree", level.title())
            elif isinstance(edu, str) and level in edu.lower():
                return edu
    return "degree"
