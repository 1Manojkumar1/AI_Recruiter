"""
Embedding service for generating job description vectors.

Uses the same fallback mechanism as Part 2 (sentence-transformers with
deterministic random-projection fallback).
"""

import warnings
import logging
import numpy as np
from typing import List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model singleton
# ---------------------------------------------------------------------------
_model = None
_model_loaded = False


def _get_model():
    global _model, _model_loaded
    if _model_loaded:
        return _model
    _model_loaded = True
    try:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("Loaded sentence-transformers model")
        return _model
    except Exception as exc:
        logger.warning("Could not load sentence-transformers: %s. Using fallback.", exc)
        _model = None
        return None


# ---------------------------------------------------------------------------
# Fallback: deterministic random projection
# ---------------------------------------------------------------------------
_RNG = np.random.default_rng(42)
_VOCAB_SIZE = 2048
_DIM = 384
_PROJECTION: Optional[np.ndarray] = None


def _get_projection() -> np.ndarray:
    global _PROJECTION
    if _PROJECTION is None:
        _PROJECTION = _RNG.standard_normal((_VOCAB_SIZE, _DIM)).astype(np.float32)
    return _PROJECTION


def _tokenize_hash(text: str) -> List[int]:
    return [hash(w) % _VOCAB_SIZE for w in text.lower().split() if w]


def _fallback_encode(texts: List[str]) -> np.ndarray:
    proj = _get_projection()
    embeddings = []
    for text in texts:
        indices = _tokenize_hash(text)
        if not indices:
            embeddings.append(np.zeros(_DIM, dtype=np.float32))
            continue
        vec = np.zeros(_VOCAB_SIZE, dtype=np.float32)
        for idx in indices:
            vec[idx] += 1.0
        vec /= max(len(indices), 1)
        emb = vec @ proj
        norm = np.linalg.norm(emb)
        if norm > 0:
            emb /= norm
        embeddings.append(emb)
    return np.stack(embeddings)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_embedding(text: str) -> List[float]:
    """
    Generate a 384-dimensional embedding for text.

    Parameters
    ----------
    text : str
        Input text (job description or search query).

    Returns
    -------
    list[float]
        384-dim embedding vector.
    """
    if not text or not text.strip():
        return [0.0] * 384

    model = _get_model()
    if model is not None:
        try:
            emb = model.encode(
                [text], batch_size=1, show_progress_bar=False, normalize_embeddings=True
            )
            return emb[0].tolist()
        except Exception as exc:
            logger.warning("Model encode failed (%s), using fallback", exc)

    return _fallback_encode([text])[0].tolist()


def generate_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for multiple texts."""
    if not texts:
        return []

    model = _get_model()
    if model is not None:
        try:
            embs = model.encode(
                texts, batch_size=64, show_progress_bar=False, normalize_embeddings=True
            )
            return [e.tolist() for e in embs]
        except Exception as exc:
            logger.warning("Batch encode failed (%s), using fallback", exc)

    result = _fallback_encode(texts)
    return [e.tolist() for e in result]
