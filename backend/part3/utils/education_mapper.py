"""
Education level mapping and scoring.

Maps degree names to hierarchy levels and computes education scores
with tier and GPA bonuses.
"""

from typing import Dict, Optional, Any


# ---------------------------------------------------------------------------
# Degree level hierarchy (higher = more education)
# ---------------------------------------------------------------------------
DEGREE_HIERARCHY: Dict[str, int] = {
    "phd": 6,
    "doctorate": 6,
    "d.phil": 6,
    "m.s.": 5,
    "ms": 5,
    "m.sc": 5,
    "m.sc.": 5,
    "m.e.": 5,
    "me": 5,
    "m.tech": 5,
    "mtech": 5,
    "mba": 5,
    "m.eng": 5,
    "masters": 5,
    "master": 5,
    "master's": 5,
    "b.e.": 4,
    "be": 4,
    "b.tech": 4,
    "btech": 4,
    "b.sc": 4,
    "b.sc.": 4,
    "bachelors": 4,
    "bachelor": 4,
    "bachelor's": 4,
    "bachelor of engineering": 4,
    "bachelor of science": 4,
    "associate": 3,
    "diploma": 2,
    "certificate": 1,
}


# ---------------------------------------------------------------------------
# Degree name normalisation
# ---------------------------------------------------------------------------
_DEGREE_ALIASES: Dict[str, str] = {
    "m.s": "m.s.",
    "m sc": "m.sc",
    "m.sc ": "m.sc.",
    "m e": "m.e.",
    "m tech": "m.tech",
    "b.e": "b.e.",
    "b sc": "b.sc",
    "b tech": "b.tech",
    "bachelor of engineering": "b.e.",
    "bachelor of science": "b.sc",
    "master of science": "m.sc",
    "master of engineering": "m.e.",
    "master of technology": "m.tech",
    "master of business administration": "mba",
}


def normalise_degree(degree: str) -> str:
    """Normalise a degree name to canonical lowercase form."""
    d = degree.strip().lower()
    d = _DEGREE_ALIASES.get(d, d)
    return d


def get_degree_level(degree: str) -> int:
    """
    Return the hierarchy level for a degree.

    Parameters
    ----------
    degree : str
        Degree name (e.g. "M.S.", "B.Tech", "PhD").

    Returns
    -------
    int
        Level from 1 (certificate) to 6 (PhD). Returns 0 if unknown.
    """
    norm = normalise_degree(degree)
    return DEGREE_HIERARCHY.get(norm, 0)


def calculate_education_score(
    candidate_education: list,
    required_education: str = "",
) -> float:
    """
    Compute education score (0-100) for a candidate.

    Scoring logic:
    - Base score from degree level (PhD=100, Masters=90, Bachelors=80, etc.)
    - Bonus for tier_1/tier_2 institutions
    - Bonus for strong GPA/grade
    - Penalty if candidate's degree is below requirement

    Parameters
    ----------
    candidate_education : list[dict]
        List of education records from Part 1. Each dict may have:
        ``degree``, ``institution``, ``grade``, ``tier``.
    required_education : str
        Minimum degree required by the job (e.g. "Bachelors").

    Returns
    -------
    float
        Score in 0-100.
    """
    if not candidate_education:
        return 40.0  # neutral when no education data

    # Find highest degree level
    best_level = 0
    best_tier = ""
    best_grade = 0.0

    for edu in candidate_education:
        degree = edu.get("degree", "")
        level = get_degree_level(degree)
        if level > best_level:
            best_level = level
            best_tier = (edu.get("tier") or "").lower().strip()
            best_grade = _parse_grade(edu.get("grade", ""))

    if best_level == 0:
        return 40.0

    # Base score from degree level
    level_scores = {6: 100, 5: 90, 4: 80, 3: 70, 2: 60, 1: 50}
    base = level_scores.get(best_level, 40)

    # Tier bonus
    tier_bonus = 0
    if "tier_1" in best_tier:
        tier_bonus = 10
    elif "tier_2" in best_tier:
        tier_bonus = 5

    # Grade bonus (up to 5 points)
    grade_bonus = 0
    if best_grade >= 85:
        grade_bonus = 5
    elif best_grade >= 75:
        grade_bonus = 3
    elif best_grade >= 65:
        grade_bonus = 1

    # Penalty if below requirement
    penalty = 0
    if required_education:
        req_level = get_degree_level(required_education)
        if req_level > 0 and best_level < req_level:
            penalty = (req_level - best_level) * 10

    score = base + tier_bonus + grade_bonus - penalty
    return float(max(0, min(100, score)))


def _parse_grade(grade_str: str) -> float:
    """
    Extract a numeric grade (0-100) from a grade string.

    Handles formats like "85%", "8.5 CGPA", "First Class", etc.
    """
    if not grade_str:
        return 0.0

    import re

    # Try percentage
    match = re.search(r"(\d+(?:\.\d+)?)\s*%", grade_str)
    if match:
        return float(match.group(1))

    # Try CGPA (assume /10 scale)
    match = re.search(r"(\d+(?:\.\d+)?)\s*CGPA", grade_str, re.IGNORECASE)
    if match:
        return float(match.group(1)) * 10.0

    # Try plain number
    match = re.search(r"(\d+(?:\.\d+)?)", grade_str)
    if match:
        val = float(match.group(1))
        if val <= 10.0:
            return val * 10.0
        return val

    # Text grades
    lower = grade_str.lower()
    if "first class" in lower or "distinction" in lower:
        return 85.0
    if "second class" in lower or "upper" in lower:
        return 70.0
    if "third class" in lower or "lower" in lower:
        return 55.0

    return 0.0
