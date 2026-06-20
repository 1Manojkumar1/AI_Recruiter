"""
Domain matching engine.

Compares the candidate's domain expertise against the job's industry/domain.
"""

from typing import Dict, List


def calculate_domain_score(
    candidate_domains: Dict[str, float],
    required_domains: List[str],
) -> float:
    """
    Score domain match.

    Parameters
    ----------
    candidate_domains : dict
        ``{domain: score}`` from Part 1.
    required_domains : list
        Domains specified in the job description.

    Returns
    -------
    float
        Score in 0-100.
    """
    if not required_domains:
        return 70.0  # neutral when not specified

    cand_domains = {d.lower(): s for d, s in candidate_domains.items()}
    req_domains = [d.lower() for d in required_domains]

    matched = 0.0
    for req in req_domains:
        if req in cand_domains:
            matched += cand_domains[req]
        else:
            # Partial match: check if any candidate domain contains the req
            for cd, cs in cand_domains.items():
                if req in cd or cd in req:
                    matched += cs * 0.5
                    break

    score = (matched / len(req_domains)) * 100
    return round(min(100, max(0, score)), 2)


def get_matched_domains(
    candidate_domains: Dict[str, float],
    required_domains: List[str],
) -> List[str]:
    """Return list of matched domain names."""
    cand_set = {d.lower() for d in candidate_domains.keys()}
    req_set = {d.lower() for d in required_domains}
    return sorted(cand_set & req_set)
