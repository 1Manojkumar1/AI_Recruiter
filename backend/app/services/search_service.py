"""
Search service for candidate retrieval.

Loads candidates from Part 1 output and provides numpy-based brute-force
cosine similarity search.
"""

import json
import logging
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from ..config.settings import get_settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Global state
# ---------------------------------------------------------------------------
_candidates: List[Dict[str, Any]] = []
_embeddings: Optional[np.ndarray] = None
_loaded = False


def _load_candidates() -> None:
    """Load candidates and build numpy index."""
    global _candidates, _embeddings, _loaded
    if _loaded:
        return

    settings = get_settings()
    path = settings.PROCESSED_CANDIDATES_PATH

    if not path.exists():
        logger.error("Candidates file not found: %s", path)
        _loaded = True
        return

    logger.info("Loading candidates from %s...", path.name)
    _candidates = []
    embeddings_list = []

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            _candidates.append(rec)
            emb = rec.get("candidate_embedding", [])
            if emb and len(emb) == 384:
                embeddings_list.append(emb)
            else:
                embeddings_list.append([0.0] * 384)

    if embeddings_list:
        _embeddings = np.array(embeddings_list, dtype=np.float32)
        norms = np.linalg.norm(_embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        _embeddings = _embeddings / norms

    _loaded = True
    logger.info("Loaded %d candidates (%d with valid embeddings)", len(_candidates), len(embeddings_list))


def ensure_loaded() -> int:
    """Ensure candidates are loaded. Returns count."""
    _load_candidates()
    return len(_candidates)


def get_candidate_count() -> int:
    """Return number of loaded candidates."""
    _load_candidates()
    return len(_candidates)


def get_candidate_by_id(candidate_id: str) -> Optional[Dict[str, Any]]:
    """Find a candidate by ID."""
    _load_candidates()
    for c in _candidates:
        cid = c.get("candidate_id") or c.get("id", "")
        if cid == candidate_id:
            return c
    return None


def search_candidates(
    query_embedding: List[float],
    top_k: int = 100,
) -> List[Dict[str, Any]]:
    """
    Retrieve top-k candidates by cosine similarity.

    Parameters
    ----------
    query_embedding : list[float]
        384-dim query embedding.
    top_k : int
        Number of results to return.

    Returns
    -------
    list[dict]
        Candidates with added 'search_score' field, sorted by similarity.
    """
    _load_candidates()

    if not _candidates or _embeddings is None:
        return []

    query = np.array(query_embedding, dtype=np.float32).reshape(1, -1)
    norm = np.linalg.norm(query)
    if norm > 0:
        query = query / norm

    k = min(top_k, len(_candidates))
    sims = (_embeddings @ query.T).flatten()
    top_idx = np.argpartition(sims, -k)[-k:]
    top_idx = top_idx[np.argsort(sims[top_idx])[::-1]]

    results = []
    for idx in top_idx:
        idx = int(idx)
        cand = _candidates[idx].copy()
        cand["search_score"] = float(sims[idx])
        results.append(cand)

    return results
