"""
Tests for embedding generation (Part 7 - Performance & Correctness).
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import numpy as np
from backend.app.services.embedding_service import generate_embedding, generate_embeddings_batch


class TestEmbeddingGeneration:

    def test_embedding_size(self):
        emb = generate_embedding("Python developer with ML experience")
        assert len(emb) == 384

    def test_embedding_is_list_of_floats(self):
        emb = generate_embedding("Senior backend engineer")
        assert isinstance(emb, list)
        assert all(isinstance(x, float) for x in emb)

    def test_no_null_embeddings(self):
        emb = generate_embedding("Test text")
        assert all(x is not None for x in emb)
        assert not all(x == 0.0 for x in emb)

    def test_embedding_normalized(self):
        emb = generate_embedding("Machine learning engineer")
        norm = np.linalg.norm(emb)
        assert abs(norm - 1.0) < 0.01

    def test_empty_text_returns_zeros(self):
        emb = generate_embedding("")
        assert len(emb) == 384
        assert all(x == 0.0 for x in emb)

    def test_similar_texts_similar_embeddings(self):
        emb1 = generate_embedding("Python developer")
        emb2 = generate_embedding("Python programmer")
        sim = np.dot(emb1, emb2)
        assert sim > 0.5

    def test_different_texts_different_embeddings(self):
        emb1 = generate_embedding("Python developer")
        emb2 = generate_embedding("Marketing manager")
        sim = np.dot(emb1, emb2)
        assert sim < 0.8

    def test_batch_embeddings(self):
        texts = ["Python developer", "Java developer", "Data scientist"]
        embeddings = generate_embeddings_batch(texts)
        assert len(embeddings) == 3
        assert all(len(e) == 384 for e in embeddings)

    def test_batch_empty(self):
        assert generate_embeddings_batch([]) == []
