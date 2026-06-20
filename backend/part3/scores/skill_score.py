"""
Skill match scoring.

Compares job-required skills against a candidate's skill set,
supporting exact matches, synonym matches, and preferred-skill bonuses.
"""

from typing import Dict, List, Set, Tuple

from ..utils.skill_mapper import normalise_skill, find_best_skill_match
from ..utils.weights import SKILL_REQUIRED_WEIGHT, SKILL_PREFERRED_WEIGHT


def calculate_skill_score(
    candidate_skills: Dict[str, float],
    required_skills: List[str],
    preferred_skills: List[str] = None,
) -> Tuple[float, Dict[str, Any]]:
    """
    Score how well a candidate's skills match the job requirements.

    Parameters
    ----------
    candidate_skills : dict
        ``{skill_name: proficiency_score}`` from Part 1.
    required_skills : list[str]
        Skills the job requires.
    preferred_skills : list[str], optional
        Skills the job prefers (nice-to-have).

    Returns
    -------
    tuple of (score: float, details: dict)
        Score in 0-100.  Details contain matched/missing breakdown.
    """
    from typing import Any

    preferred_skills = preferred_skills or []

    if not required_skills and not preferred_skills:
        return 50.0, {
            "matched_required": [],
            "matched_preferred": [],
            "missing_required": [],
            "missing_preferred": [],
            "related_matches": [],
        }

    cand_names = list(candidate_skills.keys())

    # --- Required skills matching ---
    matched_required: List[str] = []
    missing_required: List[str] = []
    related_matches: List[str] = []

    for req in required_skills:
        best_match, strength = find_best_skill_match(req, cand_names)
        if strength >= 1.0:
            matched_required.append(req)
        elif strength >= 0.5:
            related_matches.append(f"{req} (via {best_match})")
        else:
            missing_required.append(req)

    # --- Preferred skills matching ---
    matched_preferred: List[str] = []
    missing_preferred: List[str] = []

    for pref in preferred_skills:
        best_match, strength = find_best_skill_match(pref, cand_names)
        if strength >= 0.5:
            matched_preferred.append(pref)
        else:
            missing_preferred.append(pref)

    # --- Score calculation ---
    req_count = len(required_skills)
    pref_count = len(preferred_skills)

    if req_count > 0:
        # Exact matches count full, related matches count half
        req_exact = len(matched_required)
        req_related = len(related_matches)
        req_score = (req_exact + 0.5 * req_related) / req_count
    else:
        req_score = 1.0 if not required_skills else 0.0

    if pref_count > 0:
        pref_score = len(matched_preferred) / pref_count
    else:
        pref_score = 0.0

    # Weighted combination
    if req_count > 0 and pref_count > 0:
        combined = SKILL_REQUIRED_WEIGHT * req_score + SKILL_PREFERRED_WEIGHT * pref_score
    elif req_count > 0:
        combined = req_score
    else:
        combined = pref_score

    score = round(combined * 100, 2)

    details = {
        "matched_required": matched_required,
        "matched_preferred": matched_preferred,
        "missing_required": missing_required,
        "missing_preferred": missing_preferred,
        "related_matches": related_matches,
        "required_count": req_count,
        "preferred_count": pref_count,
        "exact_match_count": len(matched_required),
        "related_match_count": len(related_matches),
    }

    return score, details
