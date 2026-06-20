"""
Unit tests for Part 2 modules.

Run: python -m pytest backend/part2/tests/ -v
"""

import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.part2.job_parser import JobParser
from backend.part2.skill_matcher import calculate_skill_score, get_matched_skills
from backend.part2.experience_matcher import calculate_experience_score
from backend.part2.seniority_matcher import calculate_seniority_score
from backend.part2.domain_matcher import calculate_domain_score, get_matched_domains
from backend.part2.achievement_scorer import calculate_achievement_score
from backend.part2.career_growth import calculate_growth_score
from backend.part2.ranking_engine import calculate_final_score
from backend.part2.explainer import generate_explanation


# ======================================================================
# Job Parser Tests
# ======================================================================
class TestJobParser:
    def setup_method(self):
        self.parser = JobParser()

    def test_parse_basic_jd(self):
        jd = """
        Looking for Senior Backend Engineer.
        Must Have: Python, FastAPI, Docker
        Preferred: Kafka, AWS
        Experience: 5+ years
        Domain: FinTech
        """
        result = self.parser.parse(jd)
        assert "python" in result["required_skills"]
        assert "fastapi" in result["required_skills"]
        assert "docker" in result["required_skills"]
        assert "kafka" in result["preferred_skills"]
        assert "aws" in result["preferred_skills"]
        assert result["experience"] == 5
        assert result["seniority"] == "Senior"
        assert "FinTech" in result["domains"]

    def test_parse_empty_jd(self):
        result = self.parser.parse("")
        assert result["required_skills"] == []
        assert result["preferred_skills"] == []
        assert result["experience"] == 0

    def test_parse_noisy_formatting(self):
        jd = """
        === REQUIRED ===
        • Python
        • JavaScript
        • React
        --- PREFERRED ---
        TypeScript
        GraphQL
        --- EXPERIENCE ---
        3 years minimum
        """
        result = self.parser.parse(jd)
        assert "python" in result["required_skills"]
        assert "javascript" in result["required_skills"]
        assert "react" in result["required_skills"]
        assert result["experience"] == 3

    def test_parse_unknown_seniority_defaults_to_mid(self):
        jd = "Need a developer. Python, Docker."
        result = self.parser.parse(jd)
        assert result["seniority"] == "Mid"

    def test_parse_case_insensitive(self):
        jd = "PYTHON required. Docker preferred."
        result = self.parser.parse(jd)
        assert "python" in result["required_skills"]

    def test_parse_jd_with_preferred_header(self):
        jd = """
        Must Have: Python, Go
        Nice to have: Redis, Memcached
        Experience: 7+ years
        """
        result = self.parser.parse(jd)
        assert "python" in result["required_skills"]
        assert "go" in result["required_skills"]
        assert "redis" in result["preferred_skills"]


# ======================================================================
# Skill Matcher Tests
# ======================================================================
class TestSkillMatcher:
    def test_perfect_match(self):
        cand_skills = {"python": 0.9, "docker": 0.8, "fastapi": 0.85}
        required = ["python", "docker", "fastapi"]
        score = calculate_skill_score(cand_skills, required, [])
        assert score == 100.0

    def test_partial_match(self):
        cand_skills = {"python": 0.9, "docker": 0.8}
        required = ["python", "docker", "fastapi"]
        score = calculate_skill_score(cand_skills, required, [])
        assert 60 <= score <= 70  # 2/3 required

    def test_no_match(self):
        cand_skills = {"java": 0.9, "spring": 0.8}
        required = ["python", "docker"]
        score = calculate_skill_score(cand_skills, required, [])
        assert score == 0.0

    def test_preferred_skills_bonus(self):
        cand_skills = {"python": 0.9, "kafka": 0.7}
        required = ["python"]
        preferred = ["kafka"]
        score = calculate_skill_score(cand_skills, required, preferred)
        assert score > 70  # required matched + preferred matched

    def test_no_requirements(self):
        cand_skills = {"python": 0.9}
        score = calculate_skill_score(cand_skills, [], [])
        assert score == 50.0  # neutral

    def test_empty_candidate_skills(self):
        score = calculate_skill_score({}, ["python", "docker"], [])
        assert score == 0.0

    def test_get_matched_skills(self):
        cand_skills = {"python": 0.9, "docker": 0.8, "java": 0.7}
        result = get_matched_skills(cand_skills, ["python", "docker"], ["java"])
        assert "python" in result["matched_required"]
        assert "docker" in result["matched_required"]
        assert "java" in result["matched_preferred"]
        assert result["missing_required"] == []


# ======================================================================
# Experience Matcher Tests
# ======================================================================
class TestExperienceMatcher:
    def test_meets_requirement(self):
        score = calculate_experience_score(5, 5)
        assert score >= 85

    def test_exceeds_requirement(self):
        score = calculate_experience_score(10, 5)
        assert score >= 85

    def test_below_requirement(self):
        score = calculate_experience_score(3, 5)
        assert 30 <= score <= 70

    def test_far_below(self):
        score = calculate_experience_score(1, 5)
        assert score < 30

    def test_no_requirement(self):
        score = calculate_experience_score(5, 0)
        assert score == 75.0

    def test_zero_experience(self):
        score = calculate_experience_score(0, 5)
        assert score == 0.0


# ======================================================================
# Seniority Matcher Tests
# ======================================================================
class TestSeniorityMatcher:
    def test_exact_match(self):
        assert calculate_seniority_score("Senior", "Senior") == 100.0

    def test_one_level_above(self):
        assert calculate_seniority_score("Lead", "Senior") == 85.0

    def test_two_levels_above(self):
        assert calculate_seniority_score("Staff", "Senior") == 90.0

    def test_one_level_below(self):
        assert calculate_seniority_score("Mid", "Senior") == 75.0

    def test_two_levels_below(self):
        assert calculate_seniority_score("Junior", "Senior") == 50.0

    def test_unknown_level(self):
        score = calculate_seniority_score("Unknown", "Senior")
        assert 0 <= score <= 100


# ======================================================================
# Domain Matcher Tests
# ======================================================================
class TestDomainMatcher:
    def test_exact_match(self):
        score = calculate_domain_score({"FinTech": 0.9, "Backend": 0.7}, ["FinTech"])
        assert score >= 85

    def test_no_match(self):
        score = calculate_domain_score({"Healthcare": 0.9}, ["FinTech"])
        assert score < 30

    def test_no_requirements(self):
        score = calculate_domain_score({"FinTech": 0.9}, [])
        assert score == 70.0

    def test_multiple_domains(self):
        score = calculate_domain_score(
            {"FinTech": 0.9, "Cloud": 0.7}, ["FinTech", "Cloud"]
        )
        assert score >= 80

    def test_get_matched_domains(self):
        result = get_matched_domains(
            {"FinTech": 0.9, "Cloud": 0.7}, ["FinTech", "AI/ML"]
        )
        assert "fintech" in result


# ======================================================================
# Achievement Scorer Tests
# ======================================================================
class TestAchievementScorer:
    def test_high_achievements(self):
        score = calculate_achievement_score(0.8, 0.7, 3)
        assert score >= 70

    def test_no_achievements(self):
        score = calculate_achievement_score(0.0, 0.0, 0)
        assert score == 0.0

    def test_leadership_only(self):
        score = calculate_achievement_score(1.0, 0.0, 0)
        assert 30 <= score <= 45

    def test_impact_only(self):
        score = calculate_achievement_score(0.0, 1.0, 0)
        assert 30 <= score <= 40


# ======================================================================
# Career Growth Tests
# ======================================================================
class TestCareerGrowth:
    def test_high_growth(self):
        score = calculate_growth_score(0.8, 3)
        assert score >= 80

    def test_no_growth(self):
        score = calculate_growth_score(0.0, 0)
        assert score == 0.0

    def test_moderate_growth(self):
        score = calculate_growth_score(0.5, 1)
        assert 40 <= score <= 70


# ======================================================================
# Ranking Engine Tests
# ======================================================================
class TestRankingEngine:
    def test_final_score_calculation(self):
        score = calculate_final_score(
            semantic_similarity=80,
            skill_score=90,
            experience_score=75,
            domain_score=80,
            achievement_score=60,
            education_score=70,
            growth_score=65,
        )
        assert 60 <= score <= 90

    def test_final_score_weights_sum(self):
        from backend.part2.config import (
            WEIGHT_SEMANTIC, WEIGHT_SKILL, WEIGHT_EXPERIENCE,
            WEIGHT_DOMAIN, WEIGHT_ACHIEVEMENT, WEIGHT_EDUCATION,
            WEIGHT_GROWTH,
        )
        total = (
            WEIGHT_SEMANTIC + WEIGHT_SKILL + WEIGHT_EXPERIENCE
            + WEIGHT_DOMAIN + WEIGHT_ACHIEVEMENT + WEIGHT_EDUCATION
            + WEIGHT_GROWTH
        )
        assert abs(total - 1.0) < 0.001

    def test_perfect_scores(self):
        score = calculate_final_score(100, 100, 100, 100, 100, 100, 100)
        assert score == 100.0

    def test_zero_scores(self):
        score = calculate_final_score(0, 0, 0, 0, 0, 0, 0)
        assert score == 0.0


# ======================================================================
# Explainer Tests
# ======================================================================
class TestExplainer:
    def test_generate_explanation(self):
        mock_ranked = {
            "candidate_id": "CAND_001",
            "rank": 1,
            "final_score": 92.5,
            "semantic_similarity": 85.0,
            "skill_score": 100.0,
            "experience_score": 85.0,
            "matched_required_skills": ["python", "docker"],
            "matched_preferred_skills": ["kafka"],
            "missing_required_skills": [],
            "missing_preferred_skills": ["aws"],
            "matched_domains": ["FinTech"],
            "candidate_data": {
                "seniority": "Senior",
                "total_experience_years": 7.0,
                "leadership_score": 0.6,
                "impact_score": 0.4,
                "promotion_count": 2,
                "education_score": 0.8,
                "career_growth_score": 0.7,
            },
        }
        explanation = generate_explanation(mock_ranked)
        assert explanation["candidate_id"] == "CAND_001"
        assert explanation["rank"] == 1
        assert explanation["score"] == 92.5
        assert len(explanation["reasons"]) > 0

    def test_explanation_has_reasons(self):
        mock_ranked = {
            "candidate_id": "CAND_002",
            "rank": 2,
            "final_score": 60.0,
            "semantic_similarity": 50.0,
            "skill_score": 50.0,
            "experience_score": 50.0,
            "matched_required_skills": [],
            "matched_preferred_skills": [],
            "missing_required_skills": ["python"],
            "missing_preferred_skills": [],
            "matched_domains": [],
            "candidate_data": {
                "seniority": "Junior",
                "total_experience_years": 2.0,
                "leadership_score": 0.0,
                "impact_score": 0.0,
                "promotion_count": 0,
                "education_score": 0.5,
                "career_growth_score": 0.2,
            },
        }
        explanation = generate_explanation(mock_ranked)
        assert len(explanation["reasons"]) >= 1


# ======================================================================
# Run all tests
# ======================================================================
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
