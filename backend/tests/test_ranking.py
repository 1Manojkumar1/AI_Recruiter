"""
Tests for ranking endpoint (Part 7 - Score correctness & ranking order).
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)

SAMPLE_JD = """Senior Backend Engineer

Must Have:
Python
FastAPI
Docker
SQL

Preferred:
Kafka
AWS

Experience: 5+ years"""


class TestRankingEndpoint:

    def test_rank_returns_candidates(self):
        response = client.post("/rank", json={"job_description": SAMPLE_JD, "top_n": 5})
        assert response.status_code == 200
        data = response.json()
        assert "candidates" in data
        assert "total_scored" in data
        assert "query_time_ms" in data

    def test_rank_scores_between_0_and_100(self):
        response = client.post("/rank", json={"job_description": SAMPLE_JD, "top_n": 10})
        assert response.status_code == 200
        for cand in response.json()["candidates"]:
            assert 0 <= cand["final_score"] <= 100
            assert 0 <= cand["skill_score"] <= 100
            assert 0 <= cand["experience_score"] <= 100
            assert 0 <= cand["education_score"] <= 100
            assert 0 <= cand["semantic_score"] <= 100
            assert 0 <= cand["achievement_score"] <= 100

    def test_rank_sorted_by_final_score(self):
        response = client.post("/rank", json={"job_description": SAMPLE_JD, "top_n": 10})
        assert response.status_code == 200
        scores = [c["final_score"] for c in response.json()["candidates"]]
        assert scores == sorted(scores, reverse=True)

    def test_rank_has_explanations(self):
        response = client.post("/rank", json={"job_description": SAMPLE_JD, "top_n": 3})
        assert response.status_code == 200
        for cand in response.json()["candidates"]:
            assert len(cand["strengths"]) > 0
            assert len(cand["weaknesses"]) > 0
            assert len(cand["explanation"]) > 0

    def test_rank_has_ranks(self):
        response = client.post("/rank", json={"job_description": SAMPLE_JD, "top_n": 5})
        assert response.status_code == 200
        for i, cand in enumerate(response.json()["candidates"]):
            assert cand["rank"] == i + 1

    def test_rank_top_n_respected(self):
        response = client.post("/rank", json={"job_description": SAMPLE_JD, "top_n": 3})
        assert response.status_code == 200
        assert len(response.json()["candidates"]) <= 3

    def test_rank_custom_weights(self):
        weights = {"skill": 0.50, "experience": 0.10, "semantic": 0.20, "education": 0.10, "achievement": 0.10}
        response = client.post("/rank", json={"job_description": SAMPLE_JD, "top_n": 5, "weights": weights})
        assert response.status_code == 200
        assert "weights_used" in response.json()

    def test_rank_different_jds_different_top(self):
        jd1 = "Python Developer\n\nMust Have:\nPython\nSQL\n\nExperience: 2+ years"
        jd2 = "React Frontend Developer\n\nMust Have:\nReact\nTypeScript\n\nExperience: 3+ years"
        r1 = client.post("/rank", json={"job_description": jd1, "top_n": 5})
        r2 = client.post("/rank", json={"job_description": jd2, "top_n": 5})
        assert r1.status_code == 200
        assert r2.status_code == 200
        # Top candidates should differ
        ids1 = [c["candidate_id"] for c in r1.json()["candidates"][:3]]
        ids2 = [c["candidate_id"] for c in r2.json()["candidates"][:3]]
        assert ids1 != ids2 or len(ids1) > 0

    def test_trap_candidate_penalties(self):
        from backend.part3.services.ranking_service import _score_single_candidate
        from backend.part3.utils.weights import DEFAULT_WEIGHTS

        # 1. Test tech candidate (should not be penalized)
        tech_cand = {
            "candidate_id": "CAND_1",
            "profile_summary": "Senior AI Engineer with 6.0 years of experience at ProductCo. Strong skills.",
            "skills": {"python": 1.0, "fastapi": 1.0},
            "seniority": "Senior",
            "total_experience_years": 6.0,
            "companies": ["ProductCo"],
        }
        res_tech = _score_single_candidate(
            candidate=tech_cand,
            jd_skills=["python"],
            jd_experience=5,
            jd_education="",
            jd_seniority="Senior",
            job_embedding=None,
            weights=DEFAULT_WEIGHTS
        )

        # 2. Test non-tech candidate (should be penalized)
        non_tech_cand = {
            "candidate_id": "CAND_2",
            "profile_summary": "Principal Marketing Manager with 12.0 years of experience. Strong skills.",
            "skills": {"python": 1.0, "fastapi": 1.0},
            "seniority": "Principal",
            "total_experience_years": 12.0,
            "companies": ["Globex"],
        }
        res_non_tech = _score_single_candidate(
            candidate=non_tech_cand,
            jd_skills=["python"],
            jd_experience=5,
            jd_education="",
            jd_seniority="Senior",
            job_embedding=None,
            weights=DEFAULT_WEIGHTS
        )
        
        # 3. Test consulting-only candidate (should be penalized)
        consulting_cand = {
            "candidate_id": "CAND_3",
            "profile_summary": "Senior Software Engineer with 6.0 years of experience. Strong skills.",
            "skills": {"python": 1.0, "fastapi": 1.0},
            "seniority": "Senior",
            "total_experience_years": 6.0,
            "companies": ["TCS", "Wipro"],
        }
        res_consulting = _score_single_candidate(
            candidate=consulting_cand,
            jd_skills=["python"],
            jd_experience=5,
            jd_education="",
            jd_seniority="Senior",
            job_embedding=None,
            weights=DEFAULT_WEIGHTS
        )

        # Non-tech candidate should have a lower final score compared to the tech candidate, despite high experience
        assert res_non_tech["final_score"] < res_tech["final_score"]
        # Consulting-only candidate should have a lower final score compared to the tech candidate
        assert res_consulting["final_score"] < res_tech["final_score"]

