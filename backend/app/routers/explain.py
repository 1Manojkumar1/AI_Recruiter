"""
Explanation API router.

POST /explain - Detailed AI explanation for a candidate.
POST /compare - Compare two candidates.
"""

import logging
import sys
from pathlib import Path
from fastapi import APIRouter, HTTPException

# Ensure backend's parent is on sys.path so 'backend.part2/3/4' are importable
_backend_dir = str(Path(__file__).resolve().parent.parent.parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from ..models.schemas import (
    ExplainRequest, ExplanationResponse,
    CompareRequest, ComparisonResponse,
)
from ..services.ranking_service import explain_candidate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/explain", tags=["explanations"])


@router.post("", response_model=ExplanationResponse)
async def explain(request: ExplainRequest) -> ExplanationResponse:
    """
    Generate detailed AI explanation for why a candidate is ranked at a certain position.

    Returns strengths, weaknesses, summary, recommendation, and score breakdown.
    """
    try:
        result = explain_candidate(
            candidate_id=request.candidate_id,
            job_description_text=request.job_description,
        )

        return ExplanationResponse(**result)

    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.exception("Explanation generation failed")
        raise HTTPException(status_code=500, detail=f"Explanation failed: {str(exc)}")


@router.post("/compare", response_model=ComparisonResponse)
async def compare(request: CompareRequest) -> ComparisonResponse:
    """
    Compare two candidates and explain why one ranks higher than the other.
    """
    from ..services.search_service import get_candidate_by_id, ensure_loaded
    from ..services.embedding_service import generate_embedding
    from ..services.ranking_service import _get_job_parser, _extract_title
    from backend.part3.services.ranking_service import _score_single_candidate
    from backend.part3.utils.weights import DEFAULT_WEIGHTS
    from backend.part4.comparison_engine import compare_candidates

    try:
        ensure_loaded()

        cand_a = get_candidate_by_id(request.candidate_a_id)
        cand_b = get_candidate_by_id(request.candidate_b_id)

        if cand_a is None:
            raise HTTPException(status_code=404, detail=f"Candidate not found: {request.candidate_a_id}")
        if cand_b is None:
            raise HTTPException(status_code=404, detail=f"Candidate not found: {request.candidate_b_id}")

        # Parse JD
        parser = _get_job_parser()
        parsed_jd = parser.parse(request.job_description)
        all_skills = parsed_jd.get("required_skills", []) + parsed_jd.get("preferred_skills", [])

        structured_jd = {
            "title": _extract_title(request.job_description),
            "skills": all_skills,
            "experience": parsed_jd.get("experience", 0),
            "education": "",
            "seniority": parsed_jd.get("seniority", "Mid"),
            "summary": request.job_description[:500],
        }

        job_embedding = generate_embedding(request.job_description)

        # Score both candidates
        result_a = _score_single_candidate(
            candidate=cand_a, jd_skills=all_skills,
            jd_experience=structured_jd["experience"], jd_education="",
            jd_seniority=structured_jd["seniority"],
            job_embedding=job_embedding, weights=DEFAULT_WEIGHTS,
        )
        result_b = _score_single_candidate(
            candidate=cand_b, jd_skills=all_skills,
            jd_experience=structured_jd["experience"], jd_education="",
            jd_seniority=structured_jd["seniority"],
            job_embedding=job_embedding, weights=DEFAULT_WEIGHTS,
        )

        scores_a = {k: result_a[k] for k in ["skill_score", "experience_score", "education_score",
                                                "semantic_score", "achievement_score", "final_score"]}
        scores_b = {k: result_b[k] for k in ["skill_score", "experience_score", "education_score",
                                                "semantic_score", "achievement_score", "final_score"]}

        comparison = compare_candidates(cand_a, cand_b, scores_a, scores_b, structured_jd)

        return ComparisonResponse(**comparison)

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Comparison failed")
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(exc)}")
