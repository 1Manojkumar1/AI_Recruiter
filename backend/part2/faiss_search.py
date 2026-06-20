"""
FAISS-based candidate retrieval.

Loads a pre-built FAISS index and candidate embeddings, then retrieves
the top-k most similar candidates for a given job embedding.
"""

import json
import logging
import warnings
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

import numpy as np

from .config import FAISS_INDEX, EMBEDDING_NPY, PART1_OUTPUT, DEFAULT_TOP_K, EMBEDDING_DIM

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Index cache
# ---------------------------------------------------------------------------
_index = None
_candidate_ids: List[str] = []
_candidate_data: List[Dict[str, Any]] = []


def load_index(
    index_path: Optional[Path] = None,
    candidates_path: Optional[Path] = None,
) -> None:
    """
    Load the FAISS index and candidate metadata.

    If the FAISS index file does not exist, builds a flat index from
    the embeddings numpy file or from candidate JSONL embeddings.
    """
    global _index, _candidate_ids, _candidate_data

    idx_path = index_path or FAISS_INDEX
    cand_path = candidates_path or PART1_OUTPUT

    # Load candidate data
    if not _candidate_data:
        _load_candidates(cand_path)

    # Try loading FAISS index
    try:
        import faiss
        if idx_path.exists():
            _index = faiss.read_index(str(idx_path))
            logger.info("Loaded FAISS index from %s (%d vectors)", idx_path, _index.ntotal)
            return
    except ImportError:
        warnings.warn("[faiss_search] faiss not installed. Using numpy fallback.", stacklevel=2)
    except Exception as exc:
        warnings.warn(f"[faiss_search] Could not load FAISS index: {exc}", stacklevel=2)

    # Fallback: build a flat numpy index
    _build_numpy_index()


def _load_candidates(path: Path) -> None:
    global _candidate_ids, _candidate_data
    if not path.exists():
        raise FileNotFoundError(f"Candidates file not found: {path}")

    _candidate_ids = []
    _candidate_data = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            _candidate_ids.append(rec.get("id", ""))
            _candidate_data.append(rec)
    logger.info("Loaded %d candidates from %s", len(_candidate_ids), path.name)


def _build_numpy_index() -> None:
    """Build a simple numpy-based brute-force index."""
    global _index
    embeddings = np.array(
        [d.get("candidate_embedding", []) for d in _candidate_data],
        dtype=np.float32,
    )
    if embeddings.ndim == 1 or embeddings.shape[0] == 0:
        logger.warning("No embeddings available for index building.")
        return
    # Normalize for cosine similarity via dot product
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    embeddings = embeddings / norms
    _index = _NumpyIndex(embeddings)
    logger.info("Built numpy fallback index with %d vectors", embeddings.shape[0])


class _NumpyIndex:
    """Minimal brute-force index using numpy for cosine similarity."""

    def __init__(self, vectors: np.ndarray) -> None:
        self.vectors = vectors  # shape (n, dim), already normalised
        self.ntotal = vectors.shape[0]

    def search(self, query: np.ndarray, k: int) -> Tuple[np.ndarray, np.ndarray]:
        """
        Returns (similarities, indices) of shape (1, k).
        """
        if query.ndim == 1:
            query = query.reshape(1, -1)
        # Cosine similarity via dot product (vectors are normalised)
        sims = (self.vectors @ query.T).flatten()
        k = min(k, self.ntotal)
        top_idx = np.argpartition(sims, -k)[-k:]
        top_idx = top_idx[np.argsort(sims[top_idx])[::-1]]
        return sims[top_idx].reshape(1, -1), top_idx.reshape(1, -1)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def retrieve_candidates(
    job_embedding: np.ndarray,
    top_k: int = DEFAULT_TOP_K,
) -> List[Tuple[str, float, int]]:
    """
    Retrieve the most similar candidates.

    Parameters
    ----------
    job_embedding : np.ndarray
        384-dim job description embedding.
    top_k : int
        Number of candidates to retrieve.

    Returns
    -------
    list of (candidate_id, similarity_score, original_index)
    """
    if _index is None:
        load_index()

    if _index is None or _index.ntotal == 0:
        logger.warning("No index available. Returning empty results.")
        return []

    if job_embedding.ndim == 1:
        job_embedding = job_embedding.reshape(1, -1).astype(np.float32)

    # Normalize query
    norm = np.linalg.norm(job_embedding)
    if norm > 0:
        job_embedding = job_embedding / norm

    k = min(top_k, _index.ntotal)
    scores, indices = _index.search(job_embedding, k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        idx = int(idx)
        if 0 <= idx < len(_candidate_ids):
            results.append((_candidate_ids[idx], float(score), idx))

    return results


def get_candidate(index: int) -> Optional[Dict[str, Any]]:
    """Return candidate data by index."""
    if 0 <= index < len(_candidate_data):
        return _candidate_data[index]
    return None


def get_all_candidates() -> List[Dict[str, Any]]:
    """Return all loaded candidate data."""
    if not _candidate_data:
        load_index()
    return _candidate_data


def get_candidate_count() -> int:
    return len(_candidate_data)
