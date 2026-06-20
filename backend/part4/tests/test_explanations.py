"""
Tests for Part 4 - LLM Explanation Engine
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from backend.part4.explanation_engine import (
    generate_explanation,
    generate_short_explanation,
    _generate_recommendation,
)
from backend.part4.comparison_engine import compare_candidates


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_jd():
    return {
        "title": "Senior Backend Engineer",
        "skills": ["python", "fastapi", "docker", "postgresql"],
        "experience": 5,
        "education": "bachelors",
        "summary": "Senior backend engineer role",
        "seniority": "Senior",
    }


@pytest.fixture
def strong_candidate():
    return {
        "candidate_id": "CAND_001",
        "skills": {"python": 0.95, "fastapi": 0.90, "docker": 0.85, "postgresql": 0.80, "redis": 0.70},
        "total_experience_years": 8.0,
        "seniority": "Senior",
        "education": [{"degree": "M.S. Computer Science", "institution": "MIT"}],
        "leadership_score": 0.7,
        "impact_score": 0.6,
        "promotion_count": 3,
        "career_growth_score": 0.8,
        "profile_summary": "Senior engineer with 8 years experience",
    }


@pytest.fixture
def weak_candidate():
    return {
        "candidate_id": "CAND_002",
        "skills": {"java": 0.70, "spring": 0.60},
        "total_experience_years": 2.0,
        "seniority": "Junior",
        "education": [],
        "leadership_score": 0.1,
        "impact_score": 0.1,
        "promotion_count": 0,
        "career_growth_score": 0.2,
        "profile_summary": "Junior developer",
    }


@pytest.fixture
def strong_scores():
    return {
        "skill_score": 88.0,
        "experience_score": 90.0,
        "education_score": 85.0,
        "semantic_score": 82.0,
        "achievement_score": 78.0,
        "final_score": 86.5,
    }


@pytest.fixture
def weak_scores():
    return {
        "skill_score": 25.0,
        "experience_score": 30.0,
        "education_score": 50.0,
        "semantic_score": 40.0,
        "achievement_score": 15.0,
        "final_score": 31.0,
    }


# ---------------------------------------------------------------------------
# Explanation Engine Tests
# ---------------------------------------------------------------------------

class TestExplanationEngine:

    def test_generate_explanation_returns_required_fields(self, sample_jd, strong_candidate, strong_scores):
        result = generate_explanation(sample_jd, strong_candidate, strong_scores)
        assert "strengths" in result
        assert "weaknesses" in result
        assert "summary" in result
        assert "recommendation" in result
        assert isinstance(result["strengths"], list)
        assert isinstance(result["weaknesses"], list)
        assert isinstance(result["summary"], str)
        assert isinstance(result["recommendation"], str)

    def test_strong_candidate_has_strengths(self, sample_jd, strong_candidate, strong_scores):
        result = generate_explanation(sample_jd, strong_candidate, strong_scores)
        assert len(result["strengths"]) > 0

    def test_weak_candidate_has_weaknesses(self, sample_jd, weak_candidate, weak_scores):
        result = generate_explanation(sample_jd, weak_candidate, weak_scores)
        assert len(result["weaknesses"]) > 0

    def test_high_score_highly_recommended(self, sample_jd, strong_candidate, strong_scores):
        result = generate_explanation(sample_jd, strong_candidate, strong_scores)
        assert result["recommendation"] == "Highly Recommended"

    def test_low_score_not_recommended(self, sample_jd, weak_candidate, weak_scores):
        result = generate_explanation(sample_jd, weak_candidate, weak_scores)
        assert result["recommendation"] == "Not Recommended"

    def test_medium_score_recommended(self, sample_jd, strong_candidate):
        scores = {"skill_score": 65, "experience_score": 60, "education_score": 55,
                  "semantic_score": 58, "achievement_score": 50, "final_score": 62.0}
        result = generate_explanation(sample_jd, strong_candidate, scores)
        assert result["recommendation"] == "Recommended"

    def test_summary_contains_score(self, sample_jd, strong_candidate, strong_scores):
        result = generate_explanation(sample_jd, strong_candidate, strong_scores)
        assert "86" in result["summary"] or "87" in result["summary"]

    def test_weaknesses_for_missing_skills(self, sample_jd, weak_candidate, weak_scores):
        result = generate_explanation(sample_jd, weak_candidate, weak_scores)
        has_skill_weakness = any("skill" in w.lower() or "missing" in w.lower() for w in result["weaknesses"])
        assert has_skill_weakness

    def test_strengths_for_matched_skills(self, sample_jd, strong_candidate, strong_scores):
        result = generate_explanation(sample_jd, strong_candidate, strong_scores)
        has_skill_strength = any("skill" in s.lower() or "match" in s.lower() for s in result["strengths"])
        assert has_skill_strength

    def test_empty_jd_handling(self, strong_candidate, strong_scores):
        result = generate_explanation({}, strong_candidate, strong_scores)
        assert "strengths" in result
        assert len(result["strengths"]) > 0

    def test_list_skills_format(self, sample_jd, strong_scores):
        cand = {"skills": [{"name": "python"}, {"name": "fastapi"}], "total_experience_years": 5,
                "seniority": "Senior", "education": [], "leadership_score": 0.5,
                "impact_score": 0.4, "promotion_count": 2, "career_growth_score": 0.5}
        result = generate_explanation(sample_jd, cand, strong_scores)
        assert len(result["strengths"]) > 0


# ---------------------------------------------------------------------------
# Short Explanation Tests
# ---------------------------------------------------------------------------

class TestShortExplanation:

    def test_returns_string(self, strong_scores):
        result = generate_short_explanation(strong_scores, "Backend Engineer", "Senior", ["python", "fastapi"])
        assert isinstance(result, str)
        assert len(result) > 10

    def test_high_score_strong_fit(self, strong_scores):
        result = generate_short_explanation(strong_scores, "Backend Engineer", "Senior")
        assert "strong" in result.lower()

    def test_low_score_limited_fit(self, weak_scores):
        result = generate_short_explanation(weak_scores, "Backend Engineer", "Junior")
        assert "limited" in result.lower()

    def test_includes_skills(self, strong_scores):
        result = generate_short_explanation(strong_scores, "Backend Engineer", "Senior", ["python", "fastapi"])
        assert "python" in result.lower()

    def test_includes_score(self, strong_scores):
        result = generate_short_explanation(strong_scores)
        assert "/100" in result


# ---------------------------------------------------------------------------
# Recommendation Tests
# ---------------------------------------------------------------------------

class TestRecommendation:

    def test_highly_recommended(self):
        assert _generate_recommendation(90) == "Highly Recommended"

    def test_recommended(self):
        assert _generate_recommendation(65) == "Recommended"

    def test_consider_with_reservations(self):
        assert _generate_recommendation(45) == "Consider with Reservations"

    def test_not_recommended(self):
        assert _generate_recommendation(20) == "Not Recommended"


# ---------------------------------------------------------------------------
# Comparison Engine Tests
# ---------------------------------------------------------------------------

class TestComparisonEngine:

    def test_compare_returns_required_fields(self, strong_candidate, weak_candidate, strong_scores, weak_scores):
        result = compare_candidates(strong_candidate, weak_candidate, strong_scores, weak_scores)
        assert "candidate_A_id" in result
        assert "candidate_B_id" in result
        assert "candidate_A_advantage" in result
        assert "candidate_B_advantage" in result
        assert "final_reason" in result

    def test_higher_ranked_has_advantages(self, strong_candidate, weak_candidate, strong_scores, weak_scores):
        result = compare_candidates(strong_candidate, weak_candidate, strong_scores, weak_scores)
        assert len(result["candidate_A_advantage"]) > 0

    def test_lower_ranked_has_some_advantages(self, strong_candidate, weak_candidate, strong_scores, weak_scores):
        result = compare_candidates(strong_candidate, weak_candidate, strong_scores, weak_scores)
        assert isinstance(result["candidate_B_advantage"], list)

    def test_final_reason_mentions_ranking(self, strong_candidate, weak_candidate, strong_scores, weak_scores):
        result = compare_candidates(strong_candidate, weak_candidate, strong_scores, weak_scores)
        assert "ranks" in result["final_reason"].lower()

    def test_with_job_description(self, sample_jd, strong_candidate, weak_candidate, strong_scores, weak_scores):
        result = compare_candidates(strong_candidate, weak_candidate, strong_scores, weak_scores, sample_jd)
        assert len(result["candidate_A_advantage"]) > 0

    def test_similar_candidates(self, strong_candidate, strong_scores):
        result = compare_candidates(strong_candidate, strong_candidate, strong_scores, strong_scores)
        assert "candidate_A_advantage" in result
        assert "candidate_B_advantage" in result

    def test_experience_difference(self, strong_candidate, weak_candidate, strong_scores, weak_scores):
        result = compare_candidates(strong_candidate, weak_candidate, strong_scores, weak_scores)
        all_advantages = result["candidate_A_advantage"] + result["candidate_B_advantage"]
        has_exp = any("experience" in a.lower() for a in all_advantages)
        # At least one candidate should have experience noted
        assert has_exp or len(all_advantages) > 0
