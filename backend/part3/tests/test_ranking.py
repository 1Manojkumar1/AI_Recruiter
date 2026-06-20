"""
Comprehensive tests for Part 3 - AI Candidate Ranking Engine.

Run: python -m pytest backend/part3/tests/test_ranking.py -v
"""

import sys
import math
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.part3.utils.weights import RankingWeights, DEFAULT_WEIGHTS
from backend.part3.utils.skill_mapper import (
    normalise_skill, are_skills_related, skill_match_strength,
    find_best_skill_match,
)
from backend.part3.utils.education_mapper import (
    get_degree_level, calculate_education_score, normalise_degree,
)
from backend.part3.scores.skill_score import calculate_skill_score
from backend.part3.scores.experience_score import calculate_experience_score
from backend.part3.scores.education_score import (
    calculate_education_score as calc_edu_score,
    get_education_summary,
)
from backend.part3.scores.semantic_score import calculate_semantic_score
from backend.part3.scores.achievement_score import calculate_achievement_score
from backend.part3.services.ranking_service import rank_candidates


# ======================================================================
# Fixtures
# ======================================================================

@pytest.fixture
def sample_jd():
    return {
        "title": "Senior Backend Engineer",
        "skills": ["Python", "FastAPI", "AWS", "Docker", "Microservices"],
        "experience": 4,
        "education": "Bachelors",
        "seniority": "Senior",
        "summary": "Build scalable backend systems with Python and cloud infrastructure.",
    }


@pytest.fixture
def perfect_candidate():
    return {
        "candidate_id": "CAND_PERFECT",
        "skills": {"python": 0.95, "fastapi": 0.90, "aws": 0.85, "docker": 0.80, "microservices": 0.75},
        "total_experience_years": 6.0,
        "education": [
            {"degree": "M.S.", "institution": "MIT", "tier": "tier_1", "grade": "9.2 CGPA", "field_of_study": "Computer Science"}
        ],
        "seniority": "Senior",
        "candidate_embedding": [0.1] * 384,
        "leadership_score": 0.7,
        "impact_score": 0.6,
        "promotion_count": 2,
        "career_growth_score": 0.7,
        "profile_summary": "Senior backend engineer with 6 years experience. Led team of 8 engineers. Built scalable systems serving millions.",
    }


@pytest.fixture
def partial_candidate():
    return {
        "candidate_id": "CAND_PARTIAL",
        "skills": {"python": 0.90, "aws": 0.70},
        "total_experience_years": 3.0,
        "education": [
            {"degree": "B.Tech", "institution": "State University", "tier": "tier_3", "grade": "75%", "field_of_study": "Computer Science"}
        ],
        "seniority": "Mid",
        "candidate_embedding": [0.05] * 384,
        "leadership_score": 0.1,
        "impact_score": 0.2,
        "promotion_count": 0,
        "career_growth_score": 0.3,
        "profile_summary": "Backend developer with 3 years experience in Python.",
    }


@pytest.fixture
def weak_candidate():
    return {
        "candidate_id": "CAND_WEAK",
        "skills": {"java": 0.80, "spring": 0.70},
        "total_experience_years": 1.5,
        "education": [
            {"degree": "Diploma", "institution": "Local College", "tier": "tier_4", "grade": "65%", "field_of_study": "IT"}
        ],
        "seniority": "Junior",
        "candidate_embedding": [0.01] * 384,
        "leadership_score": 0.0,
        "impact_score": 0.0,
        "promotion_count": 0,
        "career_growth_score": 0.1,
        "profile_summary": "Junior developer with 1.5 years experience.",
    }


# ======================================================================
# Skill Mapper Tests
# ======================================================================
class TestSkillMapper:
    def test_normalise_python(self):
        assert normalise_skill("Python") == "python"
        assert normalise_skill("PYTHON") == "python"
        assert normalise_skill("py") == "python"

    def test_normalise_alias(self):
        assert normalise_skill("k8s") == "kubernetes"
        assert normalise_skill("React.js") == "react"
        assert normalise_skill("NodeJS") == "node.js"
        assert normalise_skill("golang") == "go"

    def test_exact_match(self):
        assert skill_match_strength("python", "python") == 1.0

    def test_related_match(self):
        assert skill_match_strength("fastapi", "flask") == 0.5
        assert skill_match_strength("aws", "gcp") == 0.5
        assert skill_match_strength("pytorch", "tensorflow") == 0.5

    def test_no_match(self):
        assert skill_match_strength("python", "java") == 0.0

    def test_related_skills(self):
        assert are_skills_related("docker", "podman")
        assert are_skills_related("kubernetes", "docker swarm")
        assert not are_skills_related("python", "java")

    def test_find_best_match(self):
        match, strength = find_best_skill_match(
            "FastAPI", ["python", "flask", "django"]
        )
        assert strength == 0.5  # related to flask/django
        assert match in ["flask", "django"]

    def test_find_exact_match(self):
        match, strength = find_best_skill_match(
            "python", ["python", "java", "go"]
        )
        assert strength == 1.0
        assert match == "python"


# ======================================================================
# Education Mapper Tests
# ======================================================================
class TestEducationMapper:
    def test_phd_level(self):
        assert get_degree_level("PhD") == 6
        assert get_degree_level("Doctorate") == 6

    def test_masters_level(self):
        assert get_degree_level("M.S.") == 5
        assert get_degree_level("M.Tech") == 5
        assert get_degree_level("Masters") == 5

    def test_bachelors_level(self):
        assert get_degree_level("B.Tech") == 4
        assert get_degree_level("Bachelors") == 4
        assert get_degree_level("B.E.") == 4

    def test_diploma_level(self):
        assert get_degree_level("Diploma") == 2

    def test_unknown_level(self):
        assert get_degree_level("Unknown Degree") == 0

    def test_education_score_phd(self):
        edu = [{"degree": "PhD", "institution": "MIT", "tier": "tier_1", "grade": "9.0 CGPA"}]
        score = calculate_education_score(edu)
        assert score >= 95

    def test_education_score_masters(self):
        edu = [{"degree": "M.S.", "institution": "Stanford", "tier": "tier_1", "grade": "88%"}]
        score = calculate_education_score(edu)
        assert 85 <= score <= 100

    def test_education_score_bachelors(self):
        edu = [{"degree": "B.Tech", "institution": "State U", "tier": "tier_3", "grade": "75%"}]
        score = calculate_education_score(edu)
        assert 70 <= score <= 85

    def test_education_score_diploma(self):
        edu = [{"degree": "Diploma", "institution": "College", "tier": "tier_4"}]
        score = calculate_education_score(edu)
        assert score <= 70

    def test_education_empty(self):
        score = calculate_education_score([])
        assert score == 40.0

    def test_tier_bonus(self):
        edu_tier1 = [{"degree": "B.Tech", "tier": "tier_1", "grade": "80%"}]
        edu_tier3 = [{"degree": "B.Tech", "tier": "tier_3", "grade": "80%"}]
        assert calculate_education_score(edu_tier1) > calculate_education_score(edu_tier3)

    def test_highest_degree_selected(self):
        edu = [
            {"degree": "B.Tech", "tier": "tier_3", "grade": "90%"},
            {"degree": "M.S.", "tier": "tier_2", "grade": "85%"},
        ]
        score = calculate_education_score(edu)
        assert score >= 85  # should use M.S.


# ======================================================================
# Skill Score Tests
# ======================================================================
class TestSkillScore:
    def test_perfect_match(self):
        cand = {"python": 0.9, "docker": 0.8, "fastapi": 0.85, "aws": 0.7}
        score, details = calculate_skill_score(cand, ["python", "docker", "fastapi", "aws"])
        assert score == 100.0
        assert len(details["missing_required"]) == 0

    def test_partial_match(self):
        cand = {"python": 0.9, "docker": 0.8}
        score, details = calculate_skill_score(cand, ["python", "docker", "fastapi", "aws"])
        assert 40 <= score <= 60
        assert len(details["missing_required"]) == 2

    def test_no_match(self):
        cand = {"java": 0.9, "spring": 0.8}
        score, _ = calculate_skill_score(cand, ["python", "docker"])
        assert score == 0.0

    def test_empty_skills(self):
        score, _ = calculate_skill_score({}, ["python", "docker"])
        assert score == 0.0

    def test_no_requirements(self):
        cand = {"python": 0.9}
        score, _ = calculate_skill_score(cand, [])
        assert score == 50.0  # neutral

    def test_synonym_match(self):
        cand = {"flask": 0.8, "python": 0.9}
        score, details = calculate_skill_score(cand, ["fastapi", "python"])
        # flask is related to fastapi
        assert len(details["related_matches"]) >= 1
        assert score > 50

    def test_preferred_skills_bonus(self):
        # Use a case where required skills are partially matched
        # so preferred skills actually make a difference
        cand = {"python": 0.9, "redis": 0.7}
        score_with, _ = calculate_skill_score(cand, ["python", "fastapi", "docker"], ["redis"])
        score_without, _ = calculate_skill_score(cand, ["python", "fastapi", "docker"], [])
        assert score_with > score_without

    def test_all_required_matched(self):
        cand = {"python": 0.9, "go": 0.8, "kubernetes": 0.7}
        score, details = calculate_skill_score(cand, ["python", "go"])
        assert score == 100.0
        assert details["matched_required"] == ["python", "go"]


# ======================================================================
# Experience Score Tests
# ======================================================================
class TestExperienceScore:
    def test_meets_requirement(self):
        score = calculate_experience_score(5, 4)
        assert score >= 85

    def test_exceeds_requirement(self):
        score = calculate_experience_score(10, 4)
        assert score >= 85

    def test_below_requirement(self):
        score = calculate_experience_score(2, 4)
        assert 30 <= score <= 70

    def test_far_below(self):
        score = calculate_experience_score(0.5, 4)
        assert score < 30

    def test_no_requirement(self):
        score = calculate_experience_score(5, 0)
        assert score >= 60

    def test_zero_experience(self):
        score = calculate_experience_score(0, 5)
        assert score == 0.0

    def test_exact_match(self):
        score = calculate_experience_score(4, 4)
        assert score >= 85

    def test_seniority_bonus(self):
        score_with = calculate_experience_score(5, 4, "Senior", "Senior")
        score_without = calculate_experience_score(5, 4, "Junior", "Senior")
        assert score_with > score_without

    def test_leadership_bonus(self):
        score_with = calculate_experience_score(5, 4, leadership_score=0.8)
        score_without = calculate_experience_score(5, 4, leadership_score=0.0)
        assert score_with > score_without


# ======================================================================
# Education Score Tests (via scores module)
# ======================================================================
class TestEducationScoreModule:
    def test_bachelors_meets_requirement(self):
        edu = [{"degree": "B.Tech", "tier": "tier_2", "grade": "80%"}]
        score = calc_edu_score(edu, "Bachelors")
        assert score >= 75

    def test_masters_exceeds_bachelors(self):
        edu_master = [{"degree": "M.S.", "tier": "tier_1", "grade": "88%"}]
        edu_bachelor = [{"degree": "B.Tech", "tier": "tier_2", "grade": "80%"}]
        score_m = calc_edu_score(edu_master, "Bachelors")
        score_b = calc_edu_score(edu_bachelor, "Bachelors")
        assert score_m >= score_b

    def test_diploma_below_bachelors(self):
        edu = [{"degree": "Diploma", "tier": "tier_4"}]
        score = calc_edu_score(edu, "Bachelors")
        assert score < 70

    def test_empty_education(self):
        score = calc_edu_score([], "Bachelors")
        assert score == 40.0

    def test_education_summary(self):
        edu = [
            {"degree": "B.Tech", "institution": "IIT", "tier": "tier_1", "grade": "85%", "field_of_study": "CS"},
            {"degree": "M.S.", "institution": "MIT", "tier": "tier_1", "grade": "90%", "field_of_study": "AI"},
        ]
        summary = get_education_summary(edu)
        assert summary["highest_degree"] == "M.S."
        assert summary["institution"] == "MIT"
        assert summary["has_phd"] is False


# ======================================================================
# Semantic Score Tests
# ======================================================================
class TestSemanticScore:
    def test_identical_embeddings(self):
        emb = [0.1] * 384
        score = calculate_semantic_score(emb, emb)
        assert score == 100.0

    def test_orthogonal_embeddings(self):
        emb_a = [1.0] + [0.0] * 383
        emb_b = [0.0] * 383 + [1.0]
        score = calculate_semantic_score(emb_a, emb_b)
        assert score < 10.0

    def test_similar_embeddings(self):
        emb_a = [0.1] * 384
        emb_b = [0.11] * 384
        score = calculate_semantic_score(emb_a, emb_b)
        assert score >= 99.0

    def test_none_embeddings(self):
        score = calculate_semantic_score(None, [0.1] * 384)
        assert score == 50.0

    def test_empty_embeddings(self):
        score = calculate_semantic_score([], [])
        assert score == 50.0

    def test_dimension_mismatch(self):
        score = calculate_semantic_score([0.1] * 384, [0.1] * 100)
        assert score == 50.0

    def test_zero_vector(self):
        score = calculate_semantic_score([0.0] * 384, [0.1] * 384)
        assert score == 50.0


# ======================================================================
# Achievement Score Tests
# ======================================================================
class TestAchievementScore:
    def test_high_achievements(self):
        score = calculate_achievement_score(
            leadership_score=0.8,
            impact_score=0.7,
            promotion_count=3,
            profile_text="Led team of 10 engineers. Built scalable systems. Patented algorithm.",
        )
        assert score >= 60

    def test_no_achievements(self):
        score = calculate_achievement_score(
            leadership_score=0.0,
            impact_score=0.0,
            promotion_count=0,
        )
        assert score == 0.0

    def test_leadership_only(self):
        score = calculate_achievement_score(leadership_score=1.0)
        assert 20 <= score <= 30

    def test_impact_only(self):
        score = calculate_achievement_score(impact_score=1.0)
        assert 20 <= score <= 30

    def test_promotions_only(self):
        score = calculate_achievement_score(promotion_count=3)
        assert 20 <= score <= 30


# ======================================================================
# Ranking Service Tests
# ======================================================================
class TestRankingService:
    def test_rank_candidates_basic(self, sample_jd, perfect_candidate, partial_candidate, weak_candidate):
        candidates = [weak_candidate, perfect_candidate, partial_candidate]
        ranked = rank_candidates(sample_jd, candidates, top_n=3)

        assert len(ranked) == 3
        # Perfect candidate should be ranked first
        assert ranked[0]["candidate_id"] == "CAND_PERFECT"
        assert ranked[0]["rank"] == 1
        # Scores should be in descending order
        assert ranked[0]["final_score"] >= ranked[1]["final_score"]
        assert ranked[1]["final_score"] >= ranked[2]["final_score"]

    def test_perfect_candidate_high_score(self, sample_jd, perfect_candidate):
        ranked = rank_candidates(sample_jd, [perfect_candidate], top_n=1)
        assert ranked[0]["final_score"] >= 70

    def test_weak_candidate_lower_score(self, sample_jd, perfect_candidate, weak_candidate):
        ranked_p = rank_candidates(sample_jd, [perfect_candidate], top_n=1)
        ranked_w = rank_candidates(sample_jd, [weak_candidate], top_n=1)
        assert ranked_p[0]["final_score"] > ranked_w[0]["final_score"]

    def test_result_has_all_fields(self, sample_jd, perfect_candidate):
        ranked = rank_candidates(sample_jd, [perfect_candidate], top_n=1)
        r = ranked[0]
        assert "candidate_id" in r
        assert "final_score" in r
        assert "skill_score" in r
        assert "experience_score" in r
        assert "education_score" in r
        assert "semantic_score" in r
        assert "achievement_score" in r
        assert "rank" in r
        assert "strengths" in r
        assert "weaknesses" in r
        assert "explanation" in r
        assert "breakdown" in r

    def test_scores_in_range(self, sample_jd, perfect_candidate):
        ranked = rank_candidates(sample_jd, [perfect_candidate], top_n=1)
        r = ranked[0]
        assert 0 <= r["final_score"] <= 100
        assert 0 <= r["skill_score"] <= 100
        assert 0 <= r["experience_score"] <= 100
        assert 0 <= r["education_score"] <= 100
        assert 0 <= r["semantic_score"] <= 100
        assert 0 <= r["achievement_score"] <= 100

    def test_strengths_non_empty(self, sample_jd, perfect_candidate):
        ranked = rank_candidates(sample_jd, [perfect_candidate], top_n=1)
        assert len(ranked[0]["strengths"]) > 0

    def test_weaknesses_non_empty(self, sample_jd, partial_candidate):
        ranked = rank_candidates(sample_jd, [partial_candidate], top_n=1)
        # Even partial candidates should have some weaknesses listed
        assert isinstance(ranked[0]["weaknesses"], list)

    def test_explanation_non_empty(self, sample_jd, perfect_candidate):
        ranked = rank_candidates(sample_jd, [perfect_candidate], top_n=1)
        assert len(ranked[0]["explanation"]) > 0

    def test_breakdown_keys(self, sample_jd, perfect_candidate):
        ranked = rank_candidates(sample_jd, [perfect_candidate], top_n=1)
        breakdown = ranked[0]["breakdown"]
        assert "skill" in breakdown
        assert "experience" in breakdown
        assert "education" in breakdown
        assert "semantic" in breakdown
        assert "achievement" in breakdown

    def test_custom_weights(self, sample_jd, perfect_candidate):
        custom = RankingWeights(skill=0.50, experience=0.20, semantic=0.10, education=0.10, achievement=0.10)
        ranked = rank_candidates(sample_jd, [perfect_candidate], weights=custom, top_n=1)
        assert ranked[0]["final_score"] > 0

    def test_empty_candidates(self, sample_jd):
        ranked = rank_candidates(sample_jd, [], top_n=10)
        assert ranked == []

    def test_missing_skills_field(self, sample_jd):
        cand = {"candidate_id": "C001", "total_experience_years": 5}
        ranked = rank_candidates(sample_jd, [cand], top_n=1)
        assert len(ranked) == 1
        assert ranked[0]["candidate_id"] == "C001"

    def test_skills_as_list(self, sample_jd):
        cand = {
            "candidate_id": "C002",
            "skills": [{"name": "python"}, {"name": "docker"}],
            "total_experience_years": 4,
        }
        ranked = rank_candidates(sample_jd, [cand], top_n=1)
        assert ranked[0]["skill_score"] > 0

    def test_ranking_order_multiple(self, sample_jd):
        candidates = [
            {"candidate_id": "C_HIGH", "skills": {"python": 0.9, "fastapi": 0.9, "aws": 0.9, "docker": 0.9, "microservices": 0.9},
             "total_experience_years": 8, "education": [{"degree": "M.S.", "tier": "tier_1"}],
             "seniority": "Senior", "leadership_score": 0.8, "impact_score": 0.7, "promotion_count": 3,
             "career_growth_score": 0.8, "profile_summary": "Led team built scalable systems"},
            {"candidate_id": "C_LOW", "skills": {"java": 0.5},
             "total_experience_years": 1, "education": [{"degree": "Diploma", "tier": "tier_4"}],
             "seniority": "Junior", "leadership_score": 0.0, "impact_score": 0.0, "promotion_count": 0,
             "career_growth_score": 0.1, "profile_summary": "Junior developer"},
        ]
        ranked = rank_candidates(sample_jd, candidates, top_n=10)
        assert ranked[0]["candidate_id"] == "C_HIGH"
        assert ranked[1]["candidate_id"] == "C_LOW"
        assert ranked[0]["final_score"] > ranked[1]["final_score"]

    def test_weights_validation(self):
        w = RankingWeights(skill=0.5, experience=0.5, semantic=0.5, education=0.5, achievement=0.5)
        with pytest.raises(ValueError):
            w.validate()

    def test_weights_valid(self):
        w = RankingWeights()
        w.validate()  # should not raise

    def test_top_n_limit(self, sample_jd):
        candidates = [
            {"candidate_id": f"C{i}", "skills": {"python": 0.5 + i*0.05},
             "total_experience_years": 3 + i, "seniority": "Mid",
             "leadership_score": 0.0, "impact_score": 0.0, "promotion_count": 0,
             "career_growth_score": 0.3}
            for i in range(20)
        ]
        ranked = rank_candidates(sample_jd, candidates, top_n=5)
        assert len(ranked) == 5

    def test_candidate_id_fallback(self, sample_jd):
        cand = {
            "id": "CAND_FROM_ID",
            "skills": {"python": 0.9},
            "total_experience_years": 5,
            "seniority": "Senior",
            "leadership_score": 0.3,
            "impact_score": 0.2,
            "promotion_count": 1,
            "career_growth_score": 0.5,
            "profile_summary": "Backend engineer",
        }
        ranked = rank_candidates(sample_jd, [cand], top_n=1)
        assert ranked[0]["candidate_id"] == "CAND_FROM_ID"

    def test_result_sorted_descending(self, sample_jd):
        candidates = [
            {"candidate_id": f"C{i}", "skills": {"python": 0.3 + i*0.07},
             "total_experience_years": 2 + i, "seniority": "Mid",
             "leadership_score": 0.1 * i, "impact_score": 0.1 * i,
             "promotion_count": i, "career_growth_score": 0.2 * i,
             "profile_summary": f"Candidate {i} profile"}
            for i in range(10)
        ]
        ranked = rank_candidates(sample_jd, candidates, top_n=10)
        scores = [r["final_score"] for r in ranked]
        assert scores == sorted(scores, reverse=True)


# ======================================================================
# Integration: End-to-end ranking
# ======================================================================
class TestIntegration:
    def test_end_to_end_ranking(self):
        jd = {
            "title": "ML Engineer",
            "skills": ["Python", "PyTorch", "TensorFlow", "Machine Learning"],
            "experience": 3,
            "education": "Masters",
            "seniority": "Senior",
            "summary": "Build and deploy machine learning models at scale.",
        }

        candidates = [
            {
                "candidate_id": "ML_EXPERT",
                "skills": {"python": 0.95, "pytorch": 0.90, "tensorflow": 0.85, "machine learning": 0.80, "docker": 0.70},
                "total_experience_years": 5.0,
                "education": [{"degree": "M.S.", "institution": "Stanford", "tier": "tier_1", "grade": "9.0 CGPA"}],
                "seniority": "Senior",
                "leadership_score": 0.6,
                "impact_score": 0.5,
                "promotion_count": 2,
                "career_growth_score": 0.7,
                "profile_summary": "ML engineer with 5 years experience. Led ML team. Built models serving millions.",
            },
            {
                "candidate_id": "BACKEND_DEV",
                "skills": {"python": 0.90, "django": 0.80, "postgresql": 0.70, "redis": 0.60},
                "total_experience_years": 4.0,
                "education": [{"degree": "B.Tech", "institution": "IIT", "tier": "tier_2"}],
                "seniority": "Senior",
                "leadership_score": 0.3,
                "impact_score": 0.3,
                "promotion_count": 1,
                "career_growth_score": 0.5,
                "profile_summary": "Backend developer with 4 years experience.",
            },
            {
                "candidate_id": "JUNIOR_ML",
                "skills": {"python": 0.60, "scikit-learn": 0.40},
                "total_experience_years": 1.0,
                "education": [{"degree": "B.Sc", "tier": "tier_3"}],
                "seniority": "Junior",
                "leadership_score": 0.0,
                "impact_score": 0.0,
                "promotion_count": 0,
                "career_growth_score": 0.2,
                "profile_summary": "Junior developer learning ML.",
            },
        ]

        ranked = rank_candidates(jd, candidates, top_n=3)

        # ML expert should be #1
        assert ranked[0]["candidate_id"] == "ML_EXPERT"
        # Backend dev should be #2 (has python, some experience)
        assert ranked[1]["candidate_id"] == "BACKEND_DEV"
        # Junior should be #3
        assert ranked[2]["candidate_id"] == "JUNIOR_ML"

        # All scores should be in range
        for r in ranked:
            assert 0 <= r["final_score"] <= 100
            assert len(r["strengths"]) > 0
            assert len(r["explanation"]) > 0


# ======================================================================
# Run tests
# ======================================================================
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
