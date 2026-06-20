"""
Tests for explanation endpoint (Part 7 - Explanation correctness).
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


class TestExplanationEndpoint:

    def test_explain_valid_candidate(self):
        # First get a candidate from search
        search = client.post("/search", json={"query": "Python developer", "top_k": 1})
        if search.status_code != 200 or not search.json()["results"]:
            pytest.skip("No candidates available")
        cand_id = search.json()["results"][0]["candidate_id"]

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
            "candidate_id": "NONEXISTENT_999",
            "job_description": "Python Developer",
        })
        assert response.status_code == 404

    def test_explanation_has_required_fields(self):
        search = client.post("/search", json={"query": "backend engineer", "top_k": 1})
        if search.status_code != 200 or not search.json()["results"]:
            pytest.skip("No candidates available")
        cand_id = search.json()["results"][0]["candidate_id"]

        response = client.post("/explain", json={
            "candidate_id": cand_id,
            "job_description": "Backend Engineer\n\nMust Have:\nPython\nDocker",
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["strengths"], list)
        assert isinstance(data["weaknesses"], list)
        assert isinstance(data["summary"], str)
        assert isinstance(data["recommendation"], str)
        assert isinstance(data["scores"], dict)
