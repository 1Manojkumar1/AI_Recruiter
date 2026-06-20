"""
Ranking API router.

POST /rank - Multi-factor candidate ranking with explanations.
"""

import logging
import time
from fastapi import APIRouter, HTTPException

from ..models.schemas import RankRequest, RankResponse, CandidateScore
from ..services.ranking_service import rank_candidates

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/rank", tags=["ranking"])


@router.post("", response_model=RankResponse)
async def rank(request: RankRequest) -> RankResponse:
    """
    Rank candidates against a job description.

    Performs full pipeline: parse JD -> embed -> retrieve -> multi-factor rank -> explain.
    Returns top-N candidates with detailed score breakdowns and explanations.
    """
    try:
        result = rank_candidates(
            job_description_text=request.job_description,
            top_n=request.top_n,
            custom_weights=request.weights,
        )

        candidates = []
        for i, cand in enumerate(result["candidates"]):
            candidates.append(CandidateScore(
                candidate_id=cand.get("candidate_id", ""),
                rank=cand.get("rank", i + 1),
                final_score=cand.get("final_score", 0),
                skill_score=cand.get("skill_score", 0),
                experience_score=cand.get("experience_score", 0),
                education_score=cand.get("education_score", 0),
                semantic_score=cand.get("semantic_score", 0),
                achievement_score=cand.get("achievement_score", 0),
                platform_score=cand.get("platform_score", 0),
                strengths=cand.get("strengths", []),
                weaknesses=cand.get("weaknesses", []),
                explanation=cand.get("explanation", ""),
                profile_summary=cand.get("profile_summary", "")[:200] if cand.get("profile_summary") else "",
                seniority=cand.get("seniority", ""),
                total_experience_years=cand.get("total_experience_years", 0),
            ))

        return RankResponse(
            candidates=candidates,
            total_scored=result["total_scored"],
            query_time_ms=result["query_time_ms"],
            weights_used=result["weights_used"],
        )

    except Exception as exc:
        logger.exception("Ranking failed")
        raise HTTPException(status_code=500, detail=f"Ranking failed: {str(exc)}")
