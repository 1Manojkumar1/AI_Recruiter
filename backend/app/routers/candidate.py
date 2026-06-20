"""
Candidate detail API router.

GET /candidate/{candidate_id} - Full candidate profile.
"""

import logging
from fastapi import APIRouter, HTTPException

from ..models.schemas import CandidateDetailResponse
from ..services.search_service import get_candidate_by_id, ensure_loaded

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/candidate", tags=["candidate"])


@router.get("/{candidate_id}", response_model=CandidateDetailResponse)
async def get_candidate(candidate_id: str) -> CandidateDetailResponse:
    """
    Get full candidate profile by ID.

    Returns complete candidate information including profile,
    skills, experience, education, and career history.
    """
    try:
        ensure_loaded()

        cand = get_candidate_by_id(candidate_id)
        if cand is None:
            raise HTTPException(status_code=404, detail=f"Candidate not found: {candidate_id}")

        skills = cand.get("skills", {})
        if isinstance(skills, dict):
            skills_list = [{"name": k, "score": v} for k, v in skills.items()]
        elif isinstance(skills, list):
            skills_list = skills
        else:
            skills_list = []

        domains = cand.get("domains", {})
        if isinstance(domains, dict):
            domains_list = [{"name": k, "score": v} for k, v in domains.items()]
        elif isinstance(domains, list):
            domains_list = domains
        else:
            domains_list = []

        return CandidateDetailResponse(
            candidate_id=cand.get("candidate_id") or cand.get("id", ""),
            profile={
                "name": cand.get("name", cand.get("id", "")),
                "headline": cand.get("headline", cand.get("profile_summary", "")[:100]),
                "experience": f"{cand.get('total_experience_years', 0)} years",
                "location": cand.get("location", ""),
            },
            skills=skills_list,
            domains=domains_list,
            seniority=cand.get("seniority", ""),
            total_experience_years=cand.get("total_experience_years", 0),
            leadership_score=cand.get("leadership_score", 0),
            impact_score=cand.get("impact_score", 0),
            career_growth_score=cand.get("career_growth_score", 0),
            promotion_count=cand.get("promotion_count", 0),
            education_score=cand.get("education_score", 0),
            years_in_current_role=cand.get("years_in_current_role", 0),
            profile_summary=cand.get("profile_summary", ""),
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to get candidate %s", candidate_id)
        raise HTTPException(status_code=500, detail=f"Failed to get candidate: {str(exc)}")
