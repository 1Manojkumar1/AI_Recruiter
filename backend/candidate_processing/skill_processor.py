"""
Skill normalization and scoring.

Converts raw skill lists into a ``{normalised_name: score}`` dict where
the score reflects proficiency, endorsements, and skill-specific experience.
"""

import re
from typing import Dict, Any, List, Optional

from .config import (
    PROFICIENCY_WEIGHTS,
    ENDORSEMENT_MAX_FOR_SCALING,
    ENDORSEMENT_WEIGHT,
    PROFICIENCY_WEIGHT,
    EXPERIENCE_WEIGHT,
)
from .utils import clamp, safe_float, safe_int


# Canonical aliases: map common variations to one canonical name
_SKILL_ALIASES: Dict[str, str] = {
    "js": "javascript",
    "ts": "typescript",
    "py": "python",
    "tf": "tensorflow",
    "k8s": "kubernetes",
    "node": "node.js",
    "nodejs": "node.js",
    "react.js": "react",
    "vue.js": "vue",
    "next.js": "next.js",
    "nextjs": "next.js",
    "c sharp": "c#",
    "c plus plus": "c++",
    "golang": "go",
    "aws": "aws",
    "amazon web services": "aws",
    "gcp": "gcp",
    "google cloud": "gcp",
    "ms azure": "azure",
    "microsoft azure": "azure",
    "sklearn": "scikit-learn",
    "scikit learn": "scikit-learn",
    "postgres": "postgresql",
    "postgres sql": "postgresql",
    "postgresdb": "postgresql",
    "mssql": "sql server",
    "microservices": "microservices",
    "restful api": "rest api",
    "rest apis": "rest api",
    "ci cd": "ci/cd",
    "cicd": "ci/cd",
    "dev ops": "devops",
    "machine-learning": "machine learning",
    "deep-learning": "deep learning",
    "natural-language-processing": "nlp",
    "llms": "llm",
    "large-language-models": "llm",
    "large language models": "llm",
    "retrieval-augmented-generation": "rag",
    "retrieval augmented generation": "rag",
    "pytorch": "pytorch",
    "tensor flow": "tensorflow",
}


def _normalise_name(raw: str) -> str:
    """Normalise a skill name to lowercase, canonical form."""
    name = raw.strip().lower()
    name = re.sub(r"[\s_]+", " ", name)
    name = _SKILL_ALIASES.get(name, name)
    return name


def _proficiency_score(proficiency: Optional[str]) -> float:
    """Map proficiency string to a 0-1 score."""
    if not proficiency:
        return 0.5  # default when unknown
    return PROFICIENCY_WEIGHTS.get(proficiency.lower().strip(), 0.5)


def _endorsement_score(endorsements: int) -> float:
    """Scale endorsements to 0-1 with diminishing returns."""
    if endorsements <= 0:
        return 0.0
    return clamp(endorsements / ENDORSEMENT_MAX_FOR_SCALING)


def _experience_score(months: Optional[float]) -> float:
    """Map months of skill usage to a 0-1 score."""
    if months is None or months <= 0:
        return 0.0
    # 36 months (3 years) -> ~1.0
    return clamp(months / 36.0)


class SkillProcessor:
    """Normalise and score a candidate's skill list."""

    def process(self, skills: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Return ``{normalised_skill_name: score}`` sorted by descending score.

        Parameters
        ----------
        skills : list[dict]
            Raw skill records with at least ``name``.

        Returns
        -------
        dict[str, float]
        """
        scored: Dict[str, float] = {}

        for skill in skills:
            raw_name = skill.get("name") or ""
            if not raw_name.strip():
                continue

            name = _normalise_name(raw_name)
            proficiency = skill.get("proficiency")
            endorsements = safe_int(skill.get("endorsements"))
            duration = safe_float(skill.get("duration_months"))

            p_score = _proficiency_score(proficiency)
            e_score = _endorsement_score(endorsements)
            x_score = _experience_score(duration)

            composite = (
                PROFICIENCY_WEIGHT * p_score
                + ENDORSEMENT_WEIGHT * e_score
                + EXPERIENCE_WEIGHT * x_score
            )
            composite = round(clamp(composite), 4)

            # keep the higher score if a skill appears more than once
            if name in scored:
                scored[name] = max(scored[name], composite)
            else:
                scored[name] = composite

        return dict(sorted(scored.items(), key=lambda kv: kv[1], reverse=True))
