"""
Semantic similarity scoring.

Computes cosine similarity between a job description embedding and
a candidate embedding, then converts to a 0-100 score.
"""

import numpy as np
from typing import List, Optional


def calculate_semantic_score(
    job_embedding: Optional[List[float]],
    candidate_embedding: Optional[List[float]],
) -> float:
    """
    Compute semantic similarity score (0-100).

    Uses cosine similarity between the two embedding vectors.

    Parameters
    ----------
    job_embedding : list[float] or None
        384-dim job description embedding.
    candidate_embedding : list[float] or None
        384-dim candidate embedding.

    Returns
    -------
    float
        Score in 0-100 where 100 = identical meaning.
    """
    if job_embedding is None or candidate_embedding is None:
        return 50.0  # neutral when embeddings unavailable

    if len(job_embedding) == 0 or len(candidate_embedding) == 0:
        return 50.0

    try:
        job_vec = np.array(job_embedding, dtype=np.float32)
        cand_vec = np.array(candidate_embedding, dtype=np.float32)

        # Handle dimension mismatch
        if job_vec.shape != cand_vec.shape:
            return 50.0

        # Cosine similarity
        dot = np.dot(job_vec, cand_vec)
        norm_a = np.linalg.norm(job_vec)
        norm_b = np.linalg.norm(cand_vec)

        if norm_a == 0 or norm_b == 0:
            return 50.0

        cosine_sim = dot / (norm_a * norm_b)

        # Clamp to [0, 1] and convert to 0-100
        cosine_sim = max(0.0, min(1.0, cosine_sim))
        return round(cosine_sim * 100, 2)

    except Exception:
        return 50.0


def calculate_semantic_score_batch(
    job_embedding: Optional[List[float]],
    candidate_embeddings: List[Optional[List[float]]],
) -> List[float]:
    """
    Compute semantic scores for multiple candidates against one job.

    Parameters
    ----------
    job_embedding : list[float] or None
        384-dim job description embedding.
    candidate_embeddings : list[list[float] or None]
        List of candidate embeddings.

    Returns
    -------
    list[float]
        Scores in 0-100 for each candidate.
    """
    if job_embedding is None or len(job_embedding) == 0:
        return [50.0] * len(candidate_embeddings)

    try:
        job_vec = np.array(job_embedding, dtype=np.float32)
        job_norm = np.linalg.norm(job_vec)
        if job_norm == 0:
            return [50.0] * len(candidate_embeddings)
        job_vec = job_vec / job_norm
    except Exception:
        return [50.0] * len(candidate_embeddings)

    scores = []
    for cand_emb in candidate_embeddings:
        if cand_emb is None or len(cand_emb) == 0:
            scores.append(50.0)
            continue
        try:
            cand_vec = np.array(cand_emb, dtype=np.float32)
            if cand_vec.shape != job_vec.shape:
                scores.append(50.0)
                continue
            cand_norm = np.linalg.norm(cand_vec)
            if cand_norm == 0:
                scores.append(50.0)
                continue
            cosine_sim = float(np.dot(job_vec, cand_vec / cand_norm))
            cosine_sim = max(0.0, min(1.0, cosine_sim))
            scores.append(round(cosine_sim * 100, 2))
        except Exception:
            scores.append(50.0)

    return scores
