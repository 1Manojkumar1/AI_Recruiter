"""
Education scoring.

Evaluates a candidate's educational background against job requirements,
including degree level, institution tier, and grade/GPA.
"""

from typing import Dict, Any, List

from ..utils.education_mapper import calculate_education_score as _base_calc


def calculate_education_score(
    candidate_education: List[Dict[str, Any]],
    required_education: str = "",
) -> float:
    """
    Compute education score (0-100).

    Parameters
    ----------
    candidate_education : list[dict]
        Education records from Part 1. Each dict may contain:
        ``degree``, ``institution``, ``grade``, ``tier``, ``field_of_study``.
    required_education : str
        Minimum degree required (e.g. "Bachelors", "Masters").

    Returns
    -------
    float
        Score in 0-100.
    """
    return _base_calc(candidate_education, required_education)


def get_education_summary(
    candidate_education: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Extract a summary of the candidate's education.

    Returns
    -------
    dict with keys: ``highest_degree``, ``institution``, ``tier``,
    ``grade``, ``field_of_study``, ``has_phd``.
    """
    if not candidate_education:
        return {
            "highest_degree": "unknown",
            "institution": "",
            "tier": "",
            "grade": "",
            "field_of_study": "",
            "has_phd": False,
        }

    from ..utils.education_mapper import get_degree_level

    best = None
    best_level = -1

    for edu in candidate_education:
        level = get_degree_level(edu.get("degree", ""))
        if level > best_level:
            best_level = level
            best = edu

    if best is None:
        best = candidate_education[0]

    return {
        "highest_degree": best.get("degree", "unknown"),
        "institution": best.get("institution", ""),
        "tier": best.get("tier", ""),
        "grade": best.get("grade", ""),
        "field_of_study": best.get("field_of_study", ""),
        "has_phd": best_level >= 6,
    }
