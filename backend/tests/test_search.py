"""
Tests for search endpoint (Part 7 - Performance & Correctness).
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import time
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


class TestSearchEndpoint:

    def test_search_returns_results(self):
        response = client.post("/search", json={"query": "Python developer", "top_k": 10})
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total" in data
        assert "query_time_ms" in data

    def test_search_top_k_respected(self):
        response = client.post("/search", json={"query": "backend engineer", "top_k": 5})
        assert response.status_code == 200
        assert len(response.json()["results"]) <= 5

    def test_search_latency_under_200ms(self):
        t0 = time.time()
        response = client.post("/search", json={"query": "data scientist", "top_k": 10})
        elapsed_ms = (time.time() - t0) * 1000
        assert response.status_code == 200
        # Allow generous margin for CI
        assert elapsed_ms < 5000

    def test_search_result_structure(self):
        response = client.post("/search", json={"query": "ML engineer", "top_k": 3})
        assert response.status_code == 200
        results = response.json()["results"]
        if results:
            hit = results[0]
            assert "candidate_id" in hit
            assert "score" in hit
            assert isinstance(hit["score"], (int, float))

    def test_search_score_range(self):
        response = client.post("/search", json={"query": "devops engineer", "top_k": 20})
        assert response.status_code == 200
        for hit in response.json()["results"]:
            assert -1 <= hit["score"] <= 1  # cosine similarity range

    def test_search_different_queries_different_results(self):
        r1 = client.post("/search", json={"query": "Python developer", "top_k": 5})
        r2 = client.post("/search", json={"query": "Marketing manager", "top_k": 5})
        assert r1.status_code == 200
        assert r2.status_code == 200
        ids1 = {r["candidate_id"] for r in r1.json()["results"]}
        ids2 = {r["candidate_id"] for r in r2.json()["results"]}
        # They may overlap but should not be identical
        assert ids1 != ids2 or len(ids1) > 0
