"""
Search API router.

POST /search - Semantic candidate search using embeddings.
"""

import logging
import time
from fastapi import APIRouter, HTTPException

from ..models.schemas import SearchRequest, SearchResponse, SearchHit
from ..services.embedding_service import generate_embedding
from ..services.search_service import search_candidates, ensure_loaded

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=SearchResponse)
async def search(request: SearchRequest) -> SearchResponse:
    """
    Search candidates using semantic similarity.

    Accepts a natural-language query (job description or requirements)
    and returns the most similar candidates ranked by cosine similarity.
    """
    t0 = time.time()

    try:
        count = ensure_loaded()
        if count == 0:
            raise HTTPException(status_code=503, detail="No candidates loaded. Run Part 1 processing first.")

        # Generate query embedding
        query_embedding = generate_embedding(request.query)

        # Retrieve candidates
        candidates = search_candidates(query_embedding, top_k=request.top_k)

        elapsed_ms = (time.time() - t0) * 1000

        results = []
        for cand in candidates:
            results.append(SearchHit(
                candidate_id=cand.get("candidate_id") or cand.get("id", ""),
                score=round(cand.get("search_score", 0), 4),
                profile_summary=cand.get("profile_summary", "")[:200],
                seniority=cand.get("seniority", ""),
                total_experience_years=cand.get("total_experience_years", 0),
            ))

        logger.info("Search returned %d results in %.1fms", len(results), elapsed_ms)

        return SearchResponse(
            results=results,
            total=len(results),
            query_time_ms=round(elapsed_ms, 2),
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Search failed")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(exc)}")
