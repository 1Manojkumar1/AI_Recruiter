"""
Recruiter-style profile summary generator.

Creates a human-readable summary from the structured analysis outputs.
"""

from typing import Dict, Any, List


class SummaryGenerator:
    """Generate a recruiter-friendly candidate summary."""

    def generate(
        self,
        profile: Dict[str, Any],
        career_info: Dict[str, Any],
        education_info: Dict[str, Any],
        skills: Dict[str, float],
        domains: Dict[str, float],
        leadership_score: float,
        impact_score: float,
        seniority: str,
    ) -> str:
        """
        Build a paragraph summary suitable for recruiter consumption.

        Parameters
        ----------
        profile : dict
            Raw profile dict.
        career_info : dict
            Career analysis output.
        education_info : dict
            Education analysis output.
        skills : dict
            Normalised skill scores.
        domains : dict
            Domain expertise scores.
        leadership_score : float
            0-1 leadership evidence.
        impact_score : float
            0-1 impact evidence.
        seniority : str
            Classified seniority level.

        Returns
        -------
        str
        """
        parts: List[str] = []

        # --- seniority + role ---
        role = career_info.get("current_role") or profile.get("current_title") or "Professional"
        company = career_info.get("current_company") or profile.get("current_company") or ""
        years = career_info.get("total_experience_years", 0)

        intro = f"{seniority} {role}"
        if years > 0:
            intro += f" with {years:.1f} years of experience"
        if company:
            intro += f" at {company}"
        intro += "."
        parts.append(intro)

        # --- top skills ---
        top_skills = list(skills.keys())[:5]
        if top_skills:
            skill_str = ", ".join(top_skills[:3])
            remaining = top_skills[3:]
            if remaining:
                skill_str += " and " + ", ".join(remaining)
            parts.append(f"Strong expertise in {skill_str}.")

        # --- domain focus ---
        top_domains = [d for d, s in domains.items() if s > 0.15][:3]
        if top_domains:
            parts.append(f"Primary domain expertise in {', '.join(top_domains)}.")

        # --- leadership ---
        if leadership_score >= 0.5:
            parts.append("Demonstrated leadership experience managing teams and driving initiatives.")

        # --- impact ---
        if impact_score >= 0.4:
            parts.append("Track record of delivering measurable impact and business outcomes.")

        # --- education ---
        degree = education_info.get("highest_degree") or ""
        if degree and degree.lower() != "unknown":
            parts.append(f"Holds a {degree} degree.")

        return " ".join(parts)
