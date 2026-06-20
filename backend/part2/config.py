"""
Configuration for Part 2: Candidate Ranking Engine.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR: Path = Path(__file__).resolve().parent.parent
DATA_DIR: Path = BASE_DIR
PART1_OUTPUT: Path = DATA_DIR / "processed_candidates.jsonl"
FAISS_INDEX: Path = DATA_DIR / "faiss_index.bin"
EMBEDDING_NPY: Path = DATA_DIR / "candidate_embeddings.npy"

# ---------------------------------------------------------------------------
# Embedding config
# ---------------------------------------------------------------------------
EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
EMBEDDING_BATCH_SIZE: int = 128
EMBEDDING_DIM: int = 384

# ---------------------------------------------------------------------------
# Ranking weights (must sum to 1.0)
# ---------------------------------------------------------------------------
WEIGHT_SEMANTIC: float = 0.30
WEIGHT_SKILL: float = 0.25
WEIGHT_EXPERIENCE: float = 0.15
WEIGHT_DOMAIN: float = 0.10
WEIGHT_ACHIEVEMENT: float = 0.10
WEIGHT_EDUCATION: float = 0.05
WEIGHT_GROWTH: float = 0.05

# ---------------------------------------------------------------------------
# Skill matching
# ---------------------------------------------------------------------------
SKILL_REQUIRED_WEIGHT: float = 0.70
SKILL_PREFERRED_WEIGHT: float = 0.30

# ---------------------------------------------------------------------------
# Seniority level mapping
# ---------------------------------------------------------------------------
SENIORITY_LEVELS = {
    "Intern": 1,
    "Junior": 2,
    "Mid": 3,
    "Senior": 4,
    "Lead": 5,
    "Staff": 6,
    "Principal": 7,
}

# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------
DEFAULT_TOP_K: int = 100
FINAL_TOP_N: int = 20
