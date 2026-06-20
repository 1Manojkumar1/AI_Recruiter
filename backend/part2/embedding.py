"""
Embedding generation for job descriptions.

Uses sentence-transformers (all-MiniLM-L6-v2) with a deterministic
random-projection fallback when the model is unavailable.
"""

import warnings
import numpy as np
from typing import List

from .config import EMBEDDING_MODEL, EMBEDDING_BATCH_SIZE

# ---------------------------------------------------------------------------
# Lazy model singleton
# ---------------------------------------------------------------------------
_model = None


def _get_model():
    global _model
    if _model is not None:
        return _model
    try:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(EMBEDDING_MODEL)
        return _model
    except ImportError:
        warnings.warn(
            "[embedding] sentence-transformers not installed. Using fallback.",
            stacklevel=2,
        )
        return None
    except Exception as exc:
        warnings.warn(
            f"[embedding] Could not load model: {exc}. Using fallback.",
            stacklevel=2,
        )
        return None


# ---------------------------------------------------------------------------
# Fallback: deterministic random projection
# ---------------------------------------------------------------------------
_RNG = np.random.default_rng(42)
_VOCAB_SIZE = 2048
_DIM = 384
_PROJECTION = None


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

def generate_job_embedding(text: str) -> np.ndarray:
    """
    Generate a 384-dimensional embedding for a job description.

    Parameters
    ----------
    text : str
        Job description text.

    Returns
    -------
    np.ndarray of shape (384,)
    """
    model = _get_model()
    if model is not None:
        try:
            emb = model.encode(
                [text],
                batch_size=1,
                show_progress_bar=False,
                normalize_embeddings=True,
            )
            return emb[0]
        except Exception as exc:
            warnings.warn(f"[embedding] encode failed ({exc}), using fallback.", stacklevel=2)
    return _fallback_encode([text])[0]


def generate_job_embeddings_batch(texts: List[str]) -> np.ndarray:
    """
    Encode a list of job description texts.

    Returns
    -------
    np.ndarray of shape (n, 384)
    """
    model = _get_model()
    if model is not None:
        try:
            return model.encode(
                texts,
                batch_size=EMBEDDING_BATCH_SIZE,
                show_progress_bar=False,
                normalize_embeddings=True,
            )
        except Exception as exc:
            warnings.warn(f"[embedding] batch encode failed ({exc}), using fallback.", stacklevel=2)
    return _fallback_encode(texts)
