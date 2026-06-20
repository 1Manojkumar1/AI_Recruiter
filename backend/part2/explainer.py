"""
Explainable AI ranking output.

Generates human-readable explanations for why each candidate was
ranked at a particular position.
"""

from typing import Dict, Any, List


def generate_explanation(ranked_candidate: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a structured explanation for a ranked candidate.

    Parameters
    ----------
    ranked_candidate : dict
        A single entry from ranking_engine.rank_candidates() output.

    Returns
    -------
    dict with ``candidate_id``, ``rank``, ``score``, ``reasons``.
    """
    reasons: List[str] = []

    cand = ranked_candidate.get("candidate_data", {})

    # --- Skill match ---
    matched_req = ranked_candidate.get("matched_required_skills", [])
    matched_pref = ranked_candidate.get("matched_preferred_skills", [])
    missing_req = ranked_candidate.get("missing_required_skills", [])

    total_req = len(matched_req) + len(missing_req)
    if total_req > 0 and not missing_req:
        reasons.append(f"Matched all {len(matched_req)}/{total_req} required skills")
    elif matched_req:
        reasons.append(f"Matched {len(matched_req)}/{total_req} required skills")

    if matched_pref:
        reasons.append(f"Has {len(matched_pref)} preferred skill{'s' if len(matched_pref) > 1 else ''}: {', '.join(matched_pref[:3])}")

    # --- Semantic similarity ---
    sem = ranked_candidate.get("semantic_similarity", 0)
    if sem >= 80:
        reasons.append(f"Very high semantic similarity ({sem:.0f}%)")
    elif sem >= 60:
        reasons.append(f"Strong semantic similarity ({sem:.0f}%)")

    # --- Experience ---
    exp_score = ranked_candidate.get("experience_score", 0)
    cand_years = cand.get("total_experience_years", 0)
    if exp_score >= 85:
        reasons.append(f"Experience ({cand_years:.1f} yrs) meets or exceeds requirement")
    elif exp_score >= 60:
        reasons.append(f"Experience ({cand_years:.1f} yrs) is close to requirement")

    # --- Seniority ---
    sen_score = ranked_candidate.get("seniority_score", 0)
    if sen_score >= 100:
        reasons.append(f"Seniority level ({cand.get('seniority', '?')}) is exact match")
    elif sen_score >= 85:
        reasons.append(f"Seniority level ({cand.get('seniority', '?')}) is strong match")

    # --- Domain ---
    matched_dom = ranked_candidate.get("matched_domains", [])
    if matched_dom:
        reasons.append(f"Domain expertise in {', '.join(matched_dom)}")

    # --- Achievements ---
    leadership = cand.get("leadership_score", 0)
    impact = cand.get("impact_score", 0)
    promos = cand.get("promotion_count", 0)

    if leadership >= 0.5:
        reasons.append("Demonstrated leadership managing teams")
    if impact >= 0.4:
        reasons.append("Track record of measurable impact")
    if promos >= 3:
        reasons.append(f"Fast career growth ({promos} promotions)")
    elif promos >= 1:
        reasons.append(f"Career progression ({promos} promotion{'s' if promos > 1 else ''})")

    # --- Education ---
    edu = cand.get("education_score", 0)
    if edu >= 0.8:
        reasons.append("Strong educational background")
    elif edu >= 0.6:
        reasons.append("Good educational background")

    # --- Career growth ---
    growth = cand.get("career_growth_score", 0)
    if growth >= 0.6:
        reasons.append("Strong career growth trajectory")

    # Fallback if no reasons generated
    if not reasons:
        reasons.append("Profile matches job requirements")

    return {
        "candidate_id": ranked_candidate.get("candidate_id", ""),
        "rank": ranked_candidate.get("rank", 0),
        "score": ranked_candidate.get("final_score", 0),
        "reasons": reasons,
    }


def format_ranking_output(
    ranked_list: List[Dict[str, Any]],
) -> str:
    """
    Format ranked results into a human-readable string.

    Parameters
    ----------
    ranked_list : list[dict]
        Output of rank_candidates().

    Returns
    -------
    str
        Formatted multi-line string.
    """
    lines: List[str] = []
    lines.append("=" * 70)
    lines.append("  AI CANDIDATE RANKING RESULTS")
    lines.append("=" * 70)

    for rc in ranked_list:
        explanation = generate_explanation(rc)
        lines.append("")
        lines.append(f"Rank {explanation['rank']}:  {explanation['candidate_id']}")
        lines.append(f"  Score: {explanation['score']:.1f}/100")
        lines.append(f"  Reasons:")
        for reason in explanation["reasons"]:
            lines.append(f"    - {reason}")

        cand = rc.get("candidate_data", {})
        lines.append(
            f"  Profile: {cand.get('seniority', '?')} | "
            f"{cand.get('total_experience_years', 0):.1f} yrs | "
            f"{cand.get('current_role', cand.get('profile_summary', '')[:50])}"
        )

    lines.append("")
    lines.append("=" * 70)
    lines.append(f"  Total candidates ranked: {len(ranked_list)}")
    lines.append("=" * 70)

    return "\n".join(lines)
