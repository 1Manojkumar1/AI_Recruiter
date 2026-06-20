"""
Configurable scoring weights for the ranking engine.

All weights must sum to 1.0. Adjust these to change ranking behaviour
without touching any scoring logic.
"""

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class RankingWeights:
    """
    Weight configuration for the final composite score.

    Attributes
    ----------
    skill : float
        Weight for skill match score (default 0.30).
    experience : float
        Weight for experience match score (default 0.18).
    semantic : float
        Weight for semantic similarity score (default 0.22).
    education : float
        Weight for education score (default 0.08).
    achievement : float
        Weight for achievement score (default 0.10).
    platform : float
        Weight for platform activity / behavioral signals (default 0.12).
    """

    skill: float = 0.30
    experience: float = 0.18
    semantic: float = 0.22
    education: float = 0.08
    achievement: float = 0.10
    platform: float = 0.12

    def validate(self) -> None:
        """Raise ValueError if weights don't sum to ~1.0."""
        total = self.total()
        if abs(total - 1.0) > 0.001:
            raise ValueError(
                f"Weights must sum to 1.0, got {total:.4f}. "
                f"skill={self.skill}, experience={self.experience}, "
                f"semantic={self.semantic}, education={self.education}, "
                f"achievement={self.achievement}, platform={self.platform}"
            )

    def total(self) -> float:
        """Return sum of all weights."""
        return self.skill + self.experience + self.semantic + self.education + self.achievement + self.platform

    def to_dict(self) -> Dict[str, float]:
        """Return weights as a dictionary."""
        return {
            "skill": self.skill,
            "experience": self.experience,
            "semantic": self.semantic,
            "education": self.education,
            "achievement": self.achievement,
            "platform": self.platform,
        }


# Default weights instance
DEFAULT_WEIGHTS = RankingWeights()


# ---------------------------------------------------------------------------
# Skill matching weights
# ---------------------------------------------------------------------------
SKILL_REQUIRED_WEIGHT: float = 0.70
SKILL_PREFERRED_WEIGHT: float = 0.30


# ---------------------------------------------------------------------------
# Achievement bonus points
# ---------------------------------------------------------------------------
ACHIEVEMENT_BONUSES = {
    "promotion": 10,
    "leadership": 10,
    "patent": 15,
    "award": 10,
    "open_source": 8,
    "publication": 8,
    "large_scale_project": 7,
}


# ---------------------------------------------------------------------------
# Education level scores (0-100)
# ---------------------------------------------------------------------------
EDUCATION_LEVEL_SCORES: Dict[str, int] = {
    "phd": 100,
    "doctorate": 100,
    "m.s.": 90,
    "ms": 90,
    "m.sc": 90,
    "m.sc.": 90,
    "m.e.": 90,
    "me": 90,
    "m.tech": 90,
    "mtech": 90,
    "mba": 90,
    "masters": 90,
    "master": 90,
    "b.e.": 80,
    "be": 80,
    "b.tech": 80,
    "btech": 80,
    "b.sc": 80,
    "b.sc.": 80,
    "bachelors": 80,
    "bachelor": 80,
    "associate": 70,
    "diploma": 60,
}


# ---------------------------------------------------------------------------
# Tier bonuses for education
# ---------------------------------------------------------------------------
TIER_BONUSES: Dict[str, int] = {
    "tier_1": 10,
    "tier_2": 5,
    "tier_3": 0,
    "tier_4": 0,
}


# ---------------------------------------------------------------------------
# Seniority level mapping
# ---------------------------------------------------------------------------
SENIORITY_LEVELS: Dict[str, int] = {
    "intern": 1,
    "junior": 2,
    "mid": 3,
    "senior": 4,
    "lead": 5,
    "staff": 6,
    "principal": 7,
}
