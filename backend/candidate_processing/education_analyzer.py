"""
Education analysis module.

Converts raw education records into a single ``education_score`` and
extracts degree-level metadata.
"""

from typing import Dict, Any, List, Optional

from .config import (
    EDUCATION_TIER_SCORES,
    DEGREE_LEVEL_BONUS,
)
from .utils import safe_float, clamp, extract_percentage


class EducationAnalyzer:
    """Analyze education history and produce a composite score."""

    def __init__(self) -> None:
        self._tier_scores = EDUCATION_TIER_SCORES
        self._degree_bonus = {k.lower(): v for k, v in DEGREE_LEVEL_BONUS.items()}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze(self, education: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Return a dict with ``education_score`` and metadata.

        Parameters
        ----------
        education : list[dict]
            Raw education records from the candidate profile.

        Returns
        -------
        dict
            Keys: ``education_score`` (float), ``highest_degree`` (str),
            ``has_phd`` (bool), ``grade_normalized`` (float).
        """
        if not education:
            return {
                "education_score": 0.0,
                "highest_degree": "unknown",
                "has_phd": False,
                "grade_normalized": 0.0,
            }

        best_score = 0.0
        best_degree = "unknown"
        has_phd = False
        grade_values: List[float] = []

        for edu in education:
            tier = (edu.get("tier") or "").lower().strip()
            degree = edu.get("degree") or ""
            grade_raw = edu.get("grade") or ""

            # --- tier component ---
            tier_score = self._tier_scores.get(tier, 0.4)

            # --- degree level bonus ---
            degree_lower = degree.lower().strip()
            degree_bonus = self._degree_bonus.get(degree_lower, 0.0)

            # detect PhD
            if "phd" in degree_lower or "doctorate" in degree_lower:
                has_phd = True

            # --- grade component ---
            grade_pct = extract_percentage(grade_raw)
            grade_component = 0.0
            if grade_pct is not None:
                grade_component = clamp(grade_pct / 100.0) * 0.15
                grade_values.append(grade_pct / 100.0)

            # --- composite for this record ---
            record_score = clamp(tier_score * 0.75 + degree_bonus + grade_component)

            if record_score > best_score:
                best_score = record_score
                best_degree = degree or "unknown"

        avg_grade = (
            sum(grade_values) / len(grade_values) if grade_values else 0.0
        )

        return {
            "education_score": round(clamp(best_score), 4),
            "highest_degree": best_degree,
            "has_phd": has_phd,
            "grade_normalized": round(clamp(avg_grade), 4),
        }
