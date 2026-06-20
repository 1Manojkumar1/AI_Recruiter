"""
Tests for Part 5 - FastAPI Backend API
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

class TestHealth:

    def test_health_endpoint(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "candidates_loaded" in data

    def test_root_endpoint(self):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "endpoints" in data
        assert "search" in data["endpoints"]


# ---------------------------------------------------------------------------
# Search endpoint
# ---------------------------------------------------------------------------

class TestSearch:

    def test_search_returns_results(self):
        response = client.post("/search", json={"query": "Python developer", "top_k": 10})
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total" in data
        assert "query_time_ms" in data

    def test_search_response_structure(self):
        response = client.post("/search", json={"query": "Backend engineer", "top_k": 5})
        assert response.status_code == 200
        data = response.json()
        if data["results"]:
            hit = data["results"][0]
            assert "candidate_id" in hit
            assert "score" in hit

    def test_search_empty_query_fails(self):
        response = client.post("/search", json={"query": ""})
        assert response.status_code == 422  # Pydantic validation

    def test_search_respects_top_k(self):
        response = client.post("/search", json={"query": "data scientist", "top_k": 3})
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) <= 3


# ---------------------------------------------------------------------------
# Rank endpoint
# ---------------------------------------------------------------------------

class TestRank:

    def test_rank_returns_results(self):
        jd = "Senior Backend Engineer\n\nMust Have:\nPython\nFastAPI\nDocker\n\nExperience: 5+ years"
        response = client.post("/rank", json={"job_description": jd, "top_n": 5})
        assert response.status_code == 200
        data = response.json()
        assert "candidates" in data
        assert "total_scored" in data
        assert "query_time_ms" in data

    def test_rank_response_structure(self):
        jd = "Python Developer\n\nMust Have:\nPython\nSQL\n\nExperience: 3+ years"
        response = client.post("/rank", json={"job_description": jd, "top_n": 3})
        assert response.status_code == 200
        data = response.json()
        if data["candidates"]:
            cand = data["candidates"][0]
            assert "candidate_id" in cand
            assert "final_score" in cand
            assert "skill_score" in cand
            assert "experience_score" in cand
            assert "strengths" in cand
            assert "weaknesses" in cand
            assert "explanation" in cand

    def test_rank_scores_between_0_and_100(self):
        jd = "Data Engineer\n\nMust Have:\nPython\nSpark\nSQL"
        response = client.post("/rank", json={"job_description": jd, "top_n": 5})
        assert response.status_code == 200
        for cand in response.json()["candidates"]:
            assert 0 <= cand["final_score"] <= 100
            assert 0 <= cand["skill_score"] <= 100
            assert 0 <= cand["experience_score"] <= 100

    def test_rank_sorted_by_score(self):
        jd = "Full Stack Developer\n\nMust Have:\nReact\nNode.js\nJavaScript"
        response = client.post("/rank", json={"job_description": jd, "top_n": 10})
        assert response.status_code == 200
        scores = [c["final_score"] for c in response.json()["candidates"]]
        assert scores == sorted(scores, reverse=True)

    def test_rank_custom_weights(self):
        jd = "ML Engineer\n\nMust Have:\nPython\nPyTorch"
        weights = {"skill": 0.50, "experience": 0.10, "semantic": 0.20, "education": 0.10, "achievement": 0.10}
        response = client.post("/rank", json={"job_description": jd, "top_n": 3, "weights": weights})
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Explain endpoint
# ---------------------------------------------------------------------------

class TestExplain:

    def test_explain_returns_explanation(self):
        # First get a candidate ID from search
        search_resp = client.post("/search", json={"query": "Python developer", "top_k": 1})
        if search_resp.status_code == 200 and search_resp.json()["results"]:
            cand_id = search_resp.json()["results"][0]["candidate_id"]
            response = client.post("/explain", json={
                "candidate_id": cand_id,
                "job_description": "Python Developer\n\nMust Have:\nPython\nSQL",
            })
            assert response.status_code == 200
            data = response.json()
            assert "strengths" in data
            assert "weaknesses" in data
            assert "summary" in data
            assert "recommendation" in data
            assert "scores" in data

    def test_explain_invalid_candidate(self):
        response = client.post("/explain", json={
            "candidate_id": "NONEXISTENT",
            "job_description": "Python Developer",
        })
        assert response.status_code == 404
