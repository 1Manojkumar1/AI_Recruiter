"""
Seniority matching engine.

Compares the candidate's seniority level against the job requirement.
"""

from .config import SENIORITY_LEVELS


def calculate_seniority_score(candidate_seniority: str, required_seniority: str) -> float:
    """
    Score seniority match.

    - Exact match: 100
    - One level below: 75
    - Two levels below: 50
    - One level above: 85
    - Two+ levels above: 90 (overqualified, still good)

    Parameters
    ----------
    candidate_seniority : str
        Candidate's classified seniority (e.g. "Senior").
    required_seniority : str
        Job-required seniority level.

    Returns
    -------
    float
        Score in 0-100.
    """
    cand_level = SENIORITY_LEVELS.get(candidate_seniority, 3)
    req_level = SENIORITY_LEVELS.get(required_seniority, 3)

    diff = cand_level - req_level

    if diff == 0:
        return 100.0
    elif diff == 1:
        return 85.0
    elif diff == 2:
        return 90.0
    elif diff >= 3:
        return 92.0
    elif diff == -1:
        return 75.0
    elif diff == -2:
        return 50.0
    elif diff <= -3:
        return 25.0
    return 50.0
