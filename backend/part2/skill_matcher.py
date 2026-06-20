"""
Skill matching engine.

Compares job-required and job-preferred skills against a candidate's
skill set and returns a normalised score.
"""

import re
from typing import Dict, Set

from .config import SKILL_REQUIRED_WEIGHT, SKILL_PREFERRED_WEIGHT


def _normalise(name: str) -> str:
    name = name.strip().lower()
    name = re.sub(r"[\s_]+", " ", name)
    aliases = {
        "js": "javascript", "ts": "typescript", "py": "python",
        "k8s": "kubernetes", "nodejs": "node.js", "react.js": "react",
        "golang": "go", "c sharp": "c#", "c plus plus": "c++",
        "sklearn": "scikit-learn", "postgres": "postgresql",
    }
    return aliases.get(name, name)


def calculate_skill_score(
    candidate_skills: Dict[str, float],
    required_skills: list,
    preferred_skills: list,
) -> float:
    """
    Score how well a candidate's skills match the job requirements.

    Parameters
    ----------
    candidate_skills : dict
        ``{skill_name: proficiency_score}`` from Part 1.
    required_skills : list
        Skills the job *requires*.
    preferred_skills : list
        Skills the job *prefers* (nice-to-have).

    Returns
    -------
    float
        Score in 0-100.
    """
    if not required_skills and not preferred_skills:
        return 50.0  # neutral if no skills specified

    cand_set: Set[str] = {_normalise(s) for s in candidate_skills.keys()}
    req_set: Set[str] = {_normalise(s) for s in required_skills}
    pref_set: Set[str] = {_normalise(s) for s in preferred_skills}

    # --- Required skills score ---
    req_score = 0.0
    if req_set:
        matched_req = cand_set & req_set
        req_score = len(matched_req) / len(req_set)

    # --- Preferred skills score ---
    pref_score = 0.0
    if pref_set:
        matched_pref = cand_set & pref_set
        pref_score = len(matched_pref) / len(pref_set)

    # --- Weighted combination ---
    if req_set and pref_set:
        combined = SKILL_REQUIRED_WEIGHT * req_score + SKILL_PREFERRED_WEIGHT * pref_score
    elif req_set:
        combined = req_score
    else:
        combined = pref_score

    return round(combined * 100, 2)


def get_matched_skills(
    candidate_skills: Dict[str, float],
    required_skills: list,
    preferred_skills: list,
) -> Dict[str, list]:
    """Return matched required and preferred skills."""
    cand_set = {_normalise(s) for s in candidate_skills.keys()}
    req_set = {_normalise(s) for s in required_skills}
    pref_set = {_normalise(s) for s in preferred_skills}

    return {
        "matched_required": sorted(cand_set & req_set),
        "matched_preferred": sorted(cand_set & pref_set),
        "missing_required": sorted(req_set - cand_set),
        "missing_preferred": sorted(pref_set - cand_set),
    }
