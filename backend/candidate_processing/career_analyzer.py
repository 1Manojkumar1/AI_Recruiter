"""
Career history analysis.

Extracts experience metrics, detects promotions, and produces a
``career_growth_score``.
"""

from typing import Dict, Any, List

from .config import SENIORITY_TITLES_ORDERED
from .utils import safe_float, clamp


def _title_seniority_rank(title: str) -> int:
    """Return a rough seniority rank for a title string."""
    t = title.lower().strip()
    best_rank = -1
    for rank, keyword in enumerate(SENIORITY_TITLES_ORDERED):
        if keyword in t:
            best_rank = max(best_rank, rank)
    return best_rank if best_rank >= 0 else 0


def _detect_promotions(history: List[Dict[str, Any]]) -> int:
    """
    Count likely promotions by walking the career history chronologically.

    Detects:
    - Upward title-rank moves (junior -> senior)
    - Title changes within the same company (lateral -> vertical)
    - Company switches with role progression
    """
    if len(history) < 2:
        return 0

    sorted_hist = sorted(
        history,
        key=lambda h: h.get("start_date") or "9999-99-99",
    )

    promotions = 0
    prev_rank = _title_seniority_rank(sorted_hist[0].get("title", ""))
    prev_company = (sorted_hist[0].get("company") or "").lower().strip()

    for entry in sorted_hist[1:]:
        curr_rank = _title_seniority_rank(entry.get("title", ""))
        curr_company = (entry.get("company") or "").lower().strip()

        # Direct title rank increase
        if curr_rank > prev_rank:
            promotions += 1
        # Same company, different title (likely promotion or role expansion)
        elif curr_company == prev_company and curr_rank == prev_rank:
            prev_title = (sorted_hist[sorted_hist.index(entry) - 1].get("title") or "").lower()
            curr_title = entry.get("title") or ""
            # Different title at same company likely means some progression
            if prev_title != curr_title.lower() and curr_title:
                promotions += 0.5  # partial credit for role change

        prev_rank = max(prev_rank, curr_rank)
        prev_company = curr_company

    return int(promotions)


def _years_in_current_role(history: List[Dict[str, Any]]) -> float:
    """Estimate years spent in the current (most recent) role."""
    current = None
    for entry in history:
        if entry.get("is_current"):
            current = entry
            break
    if current is None:
        current = history[-1] if history else None
    if current is None:
        return 0.0

    months = safe_float(current.get("duration_months"))
    if months > 0:
        return round(months / 12.0, 2)

    start = current.get("start_date")
    if start:
        try:
            from datetime import datetime
            start_dt = datetime.strptime(start[:10], "%Y-%m-%d")
            delta = (datetime.now() - start_dt).days / 365.25
            return round(max(0.0, delta), 2)
        except (ValueError, TypeError):
            pass
    return 0.0


def _total_experience_years(profile: Dict[str, Any], history: List[Dict[str, Any]]) -> float:
    """Return total years of experience from profile or career history."""
    yoe = safe_float(profile.get("years_of_experience"))
    if yoe > 0:
        return round(yoe, 2)

    total_months = sum(safe_float(h.get("duration_months")) for h in history)
    return round(total_months / 12.0, 2) if total_months > 0 else 0.0


def _career_growth_score(
    total_years: float,
    promotions: int,
    job_switches: int,
) -> float:
    """Heuristic growth score (0-1)."""
    if total_years <= 0:
        return 0.0

    promo_rate = promotions / max(total_years, 1.0)
    promo_score = clamp(promo_rate * 3.0)

    switch_rate = job_switches / max(total_years, 1.0)
    if 0.15 <= switch_rate <= 0.6:
        switch_score = 1.0
    elif switch_rate < 0.15:
        switch_score = 0.6
    else:
        switch_score = max(0.4, 1.0 - (switch_rate - 0.6))

    exp_score = clamp(total_years / 15.0)

    return round(clamp(
        0.45 * promo_score + 0.30 * switch_score + 0.25 * exp_score
    ), 4)


class CareerAnalyzer:
    """Analyse career history for growth, promotions, and experience."""

    def analyze(
        self,
        profile: Dict[str, Any],
        career_history: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Return career analysis metrics.

        Parameters
        ----------
        profile : dict
            Top-level profile information.
        career_history : list[dict]
            Ordered career history entries.

        Returns
        -------
        dict
        """
        total_years = _total_experience_years(profile, career_history)
        current_role = profile.get("current_title") or ""
        current_company = profile.get("current_company") or ""

        promotions = _detect_promotions(career_history)
        job_switches = max(0, len(career_history) - 1)
        yicr = _years_in_current_role(career_history)
        growth = _career_growth_score(total_years, promotions, job_switches)

        return {
            "total_experience_years": total_years,
            "current_role": current_role,
            "current_company": current_company,
            "promotion_count": promotions,
            "job_switch_frequency": round(
                job_switches / max(total_years, 1.0), 4
            ),
            "years_in_current_role": yicr,
            "career_growth_score": growth,
        }
