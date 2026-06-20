"""
Pydantic request/response schemas for the API.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class SearchRequest(BaseModel):
    """Request body for POST /search."""
    query: str = Field(..., min_length=1, max_length=2000, description="Search query (job description text)")
    top_k: int = Field(default=100, ge=1, le=500, description="Number of candidates to retrieve")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "Senior Backend Engineer with Node.js and MongoDB",
                "top_k": 100,
            }
        }


class RankRequest(BaseModel):
    """Request body for POST /rank."""
    job_description: str = Field(..., min_length=1, max_length=5000, description="Full job description text")
    top_n: int = Field(default=100, ge=1, le=100, description="Number of top candidates to return")
    weights: Optional[Dict[str, float]] = Field(default=None, description="Custom ranking weights")

    class Config:
        json_schema_extra = {
            "example": {
                "job_description": "Senior Backend Engineer\n\nMust Have:\nPython\nFastAPI\nDocker\n\nExperience: 5+ years",
                "top_n": 100,
                "weights": {"skill": 0.35, "experience": 0.20, "semantic": 0.25, "education": 0.10, "achievement": 0.10},
            }
        }


class ExplainRequest(BaseModel):
    """Request body for POST /explain."""
    candidate_id: str = Field(..., min_length=1, description="Candidate ID to explain")
    job_description: str = Field(..., min_length=1, max_length=5000, description="Full job description text")

    class Config:
        json_schema_extra = {
            "example": {
                "candidate_id": "CAND_0000001",
                "job_description": "Senior Backend Engineer\n\nMust Have:\nPython\nFastAPI\nDocker",
            }
        }


class CompareRequest(BaseModel):
    """Request body for POST /compare."""
    candidate_a_id: str = Field(..., description="Higher-ranked candidate ID")
    candidate_b_id: str = Field(..., description="Lower-ranked candidate ID")
    job_description: str = Field(..., min_length=1, max_length=5000, description="Job description for context")


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class SearchHit(BaseModel):
    """Single search result."""
    candidate_id: str
    score: float
    profile_summary: str = ""
    seniority: str = ""
    total_experience_years: float = 0.0


class SearchResponse(BaseModel):
    """Response for POST /search."""
    results: List[SearchHit]
    total: int
    query_time_ms: float


class CandidateScore(BaseModel):
    """Score breakdown for a ranked candidate."""
    candidate_id: str
    rank: int
    final_score: float
    skill_score: float
    experience_score: float
    education_score: float
    semantic_score: float
    achievement_score: float
    platform_score: float = 0.0
    strengths: List[str]
    weaknesses: List[str]
    explanation: str
    profile_summary: str = ""
    seniority: str = ""
    total_experience_years: float = 0.0


class RankResponse(BaseModel):
    """Response for POST /rank."""
    candidates: List[CandidateScore]
    total_scored: int
    query_time_ms: float
    weights_used: Dict[str, float]


class ExplanationResponse(BaseModel):
    """Response for POST /explain."""
    candidate_id: str
    strengths: List[str]
    weaknesses: List[str]
    summary: str
    recommendation: str
    scores: Dict[str, float]


class ComparisonResponse(BaseModel):
    """Response for POST /compare."""
    candidate_A_id: str
    candidate_B_id: str
    candidate_A_advantage: List[str]
    candidate_B_advantage: List[str]
    final_reason: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "ok"
    version: str
    candidates_loaded: int


class SkillItem(BaseModel):
    """Single skill entry."""
    name: str
    score: float = 0.0


class DomainItem(BaseModel):
    """Single domain entry."""
    name: str
    score: float = 0.0


class CandidateProfile(BaseModel):
    """Candidate profile summary."""
    name: str = ""
    headline: str = ""
    experience: str = ""
    location: str = ""


class CandidateDetailResponse(BaseModel):
    """Full candidate detail response for GET /candidate/{id}."""
    candidate_id: str
    profile: CandidateProfile = CandidateProfile()
    skills: List[SkillItem] = []
    domains: List[DomainItem] = []
    seniority: str = ""
    total_experience_years: float = 0.0
    leadership_score: float = 0.0
    impact_score: float = 0.0
    career_growth_score: float = 0.0
    promotion_count: int = 0
    education_score: float = 0.0
    years_in_current_role: float = 0.0
    profile_summary: str = ""


class ErrorResponse(BaseModel):
    """Error response."""
    detail: str
    code: str = "INTERNAL_ERROR"
