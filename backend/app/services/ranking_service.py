"""
Ranking service that bridges Part 2's job parser, Part 3's ranking engine,
and Part 4's explanation engine into a unified API service.
"""

import logging
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

# Ensure backend's parent is on sys.path so 'backend.part2/3/4' are importable
_backend_dir = str(Path(__file__).resolve().parent.parent.parent.parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from ..services.embedding_service import generate_embedding
from ..services.search_service import search_candidates, get_candidate_by_id, ensure_loaded

logger = logging.getLogger(__name__)

# Lazy imports to avoid circular dependencies
_job_parser = None
_ranking_weights = None


def _get_job_parser():
    global _job_parser
    if _job_parser is None:
        from backend.part2.job_parser import JobParser
        _job_parser = JobParser()
    return _job_parser


def _get_ranking_weights():
    global _ranking_weights
    if _ranking_weights is None:
        from backend.part3.utils.weights import RankingWeights
        _ranking_weights = RankingWeights
    return _ranking_weights


def rank_candidates(
    job_description_text: str,
    top_n: int = 100,
    top_k: int = 100,
    custom_weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Full ranking pipeline: parse JD -> embed -> retrieve -> rank -> explain.

    Parameters
    ----------
    job_description_text : str
        Raw job description text.
    top_n : int
        Number of top candidates to return.
    top_k : int
        Number of candidates to retrieve before ranking.
    custom_weights : dict, optional
        Custom ranking weights.

    Returns
    -------
    dict with keys: candidates, total_scored, query_time_ms, weights_used.
    """
    t0 = time.time()
    ensure_loaded()

    # 1. Parse job description
    parser = _get_job_parser()
    parsed_jd = parser.parse(job_description_text)

    # Build structured JD for Part 3
    jd_skills = parsed_jd.get("required_skills", [])
    jd_preferred = parsed_jd.get("preferred_skills", [])
    all_skills = jd_skills + jd_preferred

    structured_jd = {
        "title": _extract_title(job_description_text),
        "skills": all_skills,
        "required_skills": jd_skills,
        "preferred_skills": jd_preferred,
        "experience": parsed_jd.get("experience", 0),
        "education": "",
        "seniority": parsed_jd.get("seniority", "Mid"),
        "summary": job_description_text[:500],
    }

    # 2. Generate job embedding
    job_embedding = generate_embedding(job_description_text)

    # 3. Retrieve candidates
    candidates = search_candidates(job_embedding, top_k=top_k)

    if not candidates:
        return {
            "candidates": [],
            "total_scored": 0,
            "query_time_ms": round((time.time() - t0) * 1000, 2),
            "weights_used": {},
        }

    # 4. Rank with Part 3
    RankingWeights = _get_ranking_weights()
    weights = None
    if custom_weights:
        try:
            weights = RankingWeights(**custom_weights)
            weights.validate()
        except Exception as exc:
            logger.warning("Invalid custom weights: %s, using defaults", exc)
            weights = None

    from backend.part3.services.ranking_service import rank_candidates as part3_rank
    ranked = part3_rank(
        job_description=structured_jd,
        candidates=candidates,
        weights=weights,
        job_embedding=job_embedding,
        top_n=top_n,
    )

    elapsed_ms = (time.time() - t0) * 1000
    w = weights or RankingWeights()

    logger.info("Ranked %d candidates in %.1fms", len(ranked), elapsed_ms)

    return {
        "candidates": ranked,
        "total_scored": len(candidates),
        "query_time_ms": round(elapsed_ms, 2),
        "weights_used": w.to_dict(),
    }


def explain_candidate(
    candidate_id: str,
    job_description_text: str,
) -> Dict[str, Any]:
    """
    Generate detailed explanation for a specific candidate.

    Parameters
    ----------
    candidate_id : str
        The candidate to explain.
    job_description_text : str
        Raw job description text.

    Returns
    -------
    dict with explanation details.
    """
    ensure_loaded()

    # Get candidate
    candidate = get_candidate_by_id(candidate_id)
    if candidate is None:
        raise ValueError(f"Candidate not found: {candidate_id}")

    # Parse JD
    parser = _get_job_parser()
    parsed_jd = parser.parse(job_description_text)
    all_skills = parsed_jd.get("required_skills", []) + parsed_jd.get("preferred_skills", [])

    structured_jd = {
        "title": _extract_title(job_description_text),
        "skills": all_skills,
        "required_skills": parsed_jd.get("required_skills", []),
        "preferred_skills": parsed_jd.get("preferred_skills", []),
        "experience": parsed_jd.get("experience", 0),
        "education": "",
        "seniority": parsed_jd.get("seniority", "Mid"),
        "summary": job_description_text[:500],
    }

    job_embedding = generate_embedding(job_description_text)

    # Score with Part 3
    from backend.part3.services.ranking_service import _score_single_candidate
    from backend.part3.utils.weights import DEFAULT_WEIGHTS

    result = _score_single_candidate(
        candidate=candidate,
        jd_skills=all_skills,
        jd_experience=structured_jd["experience"],
        jd_education="",
        jd_seniority=structured_jd["seniority"],
        job_embedding=job_embedding,
        weights=DEFAULT_WEIGHTS,
    )

    # Generate LLM explanation with Part 4
    from backend.part4.explanation_engine import generate_explanation

    scores = {
        "skill_score": result["skill_score"],
        "experience_score": result["experience_score"],
        "education_score": result["education_score"],
        "semantic_score": result["semantic_score"],
        "achievement_score": result["achievement_score"],
        "platform_score": result.get("platform_score", 0.0),
        "final_score": result["final_score"],
    }

    explanation = generate_explanation(structured_jd, candidate, scores)

    return {
        "candidate_id": candidate_id,
        "strengths": explanation["strengths"],
        "weaknesses": explanation["weaknesses"],
        "summary": explanation["summary"],
        "recommendation": explanation["recommendation"],
        "scores": scores,
    }


def _extract_title(text: str) -> str:
    """Extract a job title from the first line of the JD."""
    first_line = text.strip().split("\n")[0].strip()
    # Remove common prefixes
    for prefix in ["Job Title:", "Title:", "Position:", "Role:"]:
        if first_line.lower().startswith(prefix.lower()):
            first_line = first_line[len(prefix):].strip()
    return first_line[:100] if first_line else "Unknown Role"
