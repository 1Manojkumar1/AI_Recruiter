"""
Embedding generation using sentence-transformers.

Encodes candidate text into a dense vector for downstream similarity
ranking.  Falls back to a simple TF-IDF-style vector when the model
is unavailable.
"""

import warnings
from typing import List, Optional

import numpy as np

from .config import EMBEDDING_MODEL, EMBEDDING_BATCH_SIZE, EMBEDDING_MAX_CHARS

# ---------------------------------------------------------------------------
# Lazy model singleton
# ---------------------------------------------------------------------------
_model = None


def _get_model():
    """Load the sentence-transformer model (cached after first call)."""
    global _model
    if _model is not None:
        return _model
    try:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(EMBEDDING_MODEL)
        return _model
    except ImportError:
        warnings.warn(
            "[embedding_generator] sentence-transformers not installed. "
            "Falling back to random-projection embeddings.",
            stacklevel=2,
        )
        return None
    except Exception as exc:
        warnings.warn(
            f"[embedding_generator] Could not load model: {exc}. "
            "Falling back to random-projection embeddings.",
            stacklevel=2,
        )
        return None


# ---------------------------------------------------------------------------
# Fallback: deterministic random projection (no ML model required)
# ---------------------------------------------------------------------------
_RNG = np.random.default_rng(42)
_VOCAB_SIZE = 2048
_PROJECTION: Optional[np.ndarray] = None


def _get_projection_matrix() -> np.ndarray:
    global _PROJECTION
    if _PROJECTION is None:
        _PROJECTION = _RNG.standard_normal((_VOCAB_SIZE, 384)).astype(np.float32)
    return _PROJECTION


def _simple_tokenize(text: str) -> List[int]:
    """Hash tokens into fixed vocab indices."""
    return [hash(w) % _VOCAB_SIZE for w in text.lower().split() if w]


def _fallback_embedding(texts: List[str]) -> np.ndarray:
    """Produce embeddings via bag-of-words random projection."""
    proj = _get_projection_matrix()
    embeddings = []
    for text in texts:
        indices = _simple_tokenize(text)
        if not indices:
            embeddings.append(np.zeros(384, dtype=np.float32))
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

def build_candidate_text(
    profile: dict,
    career_history: list,
    skills: list,
    education: list,
) -> str:
    """
    Concatenate all relevant candidate fields into a single text blob
    for embedding.
    """
    parts: List[str] = []

    parts.append(profile.get("headline") or "")
    parts.append(profile.get("summary") or "")
    parts.append(profile.get("current_title") or "")

    for entry in career_history:
        parts.append(entry.get("title") or "")
        parts.append(entry.get("description") or "")

    for skill in skills:
        parts.append(skill.get("name") or "")

    for edu in education:
        parts.append(edu.get("degree") or "")
        parts.append(edu.get("field_of_study") or "")
        parts.append(edu.get("institution") or "")

    raw = " ".join(p for p in parts if p)
    return raw[:EMBEDDING_MAX_CHARS]


def generate_embeddings(texts: List[str]) -> np.ndarray:
    """
    Encode a list of text strings into embeddings.

    Parameters
    ----------
    texts : list[str]
        One text blob per candidate.

    Returns
    -------
    np.ndarray of shape ``(n, dim)``
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
            warnings.warn(
                f"[embedding_generator] encode failed ({exc}), using fallback.",
                stacklevel=2,
            )
    return _fallback_embedding(texts)
