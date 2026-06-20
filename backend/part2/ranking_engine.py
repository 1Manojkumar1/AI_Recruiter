"""
Final weighted ranking engine.

Combines all individual scores into a single composite ranking score.
"""

import logging
from typing import Dict, Any, List, Optional

import numpy as np

from .config import (
    WEIGHT_SEMANTIC, WEIGHT_SKILL, WEIGHT_EXPERIENCE,
    WEIGHT_DOMAIN, WEIGHT_ACHIEVEMENT, WEIGHT_EDUCATION,
    WEIGHT_GROWTH, FINAL_TOP_N,
)
from .skill_matcher import calculate_skill_score, get_matched_skills
from .experience_matcher import calculate_experience_score
from .seniority_matcher import calculate_seniority_score
from .domain_matcher import calculate_domain_score, get_matched_domains
from .achievement_scorer import calculate_achievement_score
from .career_growth import calculate_growth_score

logger = logging.getLogger(__name__)


def calculate_final_score(
    semantic_similarity: float,
    skill_score: float,
    experience_score: float,
    domain_score: float,
    achievement_score: float,
    education_score: float,
    growth_score: float,
) -> float:
    """
    Compute the weighted final score (0-100).

    Parameters are all in 0-100 range.
    """
    final = (
        WEIGHT_SEMANTIC * semantic_similarity
        + WEIGHT_SKILL * skill_score
        + WEIGHT_EXPERIENCE * experience_score
        + WEIGHT_DOMAIN * domain_score
        + WEIGHT_ACHIEVEMENT * achievement_score
        + WEIGHT_EDUCATION * education_score
        + WEIGHT_GROWTH * growth_score
    )
    return round(final, 2)


def rank_candidates(
    job_parsed: Dict[str, Any],
    job_embedding: np.ndarray,
    retrieved_candidates: List[tuple],
    all_candidates: List[Dict[str, Any]],
    top_n: int = FINAL_TOP_N,
) -> List[Dict[str, Any]]:
    """
    Rank retrieved candidates against the parsed job description.

    Parameters
    ----------
    job_parsed : dict
        Output of JobParser.parse().
    job_embedding : np.ndarray
        384-dim job embedding.
    retrieved_candidates : list of (candidate_id, similarity_score, index)
        Output of faiss_search.retrieve_candidates().
    all_candidates : list[dict]
        Full candidate data list.
    top_n : int
        Number of final ranked candidates to return.

    Returns
    -------
    list[dict]
        Ranked candidates with all scores and explanation data.
    """
    results = []

    for cand_id, sim_score, idx in retrieved_candidates:
        if idx >= len(all_candidates):
            continue
        cand = all_candidates[idx]

        # --- Individual scores ---
        skill_sc = calculate_skill_score(
            candidate_skills=cand.get("skills", {}),
            required_skills=job_parsed.get("required_skills", []),
            preferred_skills=job_parsed.get("preferred_skills", []),
        )
        exp_sc = calculate_experience_score(
            candidate_years=cand.get("total_experience_years", 0),
            required_years=job_parsed.get("experience", 0),
        )
        sen_sc = calculate_seniority_score(
            candidate_seniority=cand.get("seniority", "Mid"),
            required_seniority=job_parsed.get("seniority", "Mid"),
        )
        dom_sc = calculate_domain_score(
            candidate_domains=cand.get("domains", {}),
            required_domains=job_parsed.get("domains", []),
        )
        ach_sc = calculate_achievement_score(
            leadership_score=cand.get("leadership_score", 0),
            impact_score=cand.get("impact_score", 0),
            promotion_count=cand.get("promotion_count", 0),
        )
        edu_sc = cand.get("education_score", 0) * 100
        gro_sc = calculate_growth_score(
            career_growth_score=cand.get("career_growth_score", 0),
            promotion_count=cand.get("promotion_count", 0),
        )

        # Semantic similarity in 0-100
        sem_sim = max(0, min(100, sim_score * 100))

        # --- Final score ---
        final = calculate_final_score(
            semantic_similarity=sem_sim,
            skill_score=skill_sc,
            experience_score=exp_sc,
            domain_score=dom_sc,
            achievement_score=ach_sc,
            education_score=edu_sc,
            growth_score=gro_sc,
        )

        # --- Matched skills / domains for explanation ---
        matched = get_matched_skills(
            candidate_skills=cand.get("skills", {}),
            required_skills=job_parsed.get("required_skills", []),
            preferred_skills=job_parsed.get("preferred_skills", []),
        )
        matched_dom = get_matched_domains(
            candidate_domains=cand.get("domains", {}),
            required_domains=job_parsed.get("domains", []),
        )

        results.append({
            "candidate_id": cand_id,
            "final_score": final,
            "semantic_similarity": round(sem_sim, 2),
            "skill_score": skill_sc,
            "experience_score": exp_sc,
            "seniority_score": sen_sc,
            "domain_score": dom_sc,
            "achievement_score": ach_sc,
            "education_score": round(edu_sc, 2),
            "growth_score": gro_sc,
            "candidate_data": cand,
            "matched_required_skills": matched["matched_required"],
            "matched_preferred_skills": matched["matched_preferred"],
            "missing_required_skills": matched["missing_required"],
            "missing_preferred_skills": matched["missing_preferred"],
            "matched_domains": matched_dom,
        })

    # Sort by final score descending
    results.sort(key=lambda x: x["final_score"], reverse=True)

    # Assign ranks
    for rank, r in enumerate(results[:top_n], 1):
        r["rank"] = rank

    return results[:top_n]
