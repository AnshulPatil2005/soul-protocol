# test_embeddings/test_similarity.py — Tests for similarity functions.
# Created: 2026-03-06 — Covers cosine_similarity, euclidean_distance, dot_product
# with edge cases like zero vectors, identical vectors, and orthogonal vectors.

from __future__ import annotations

import math

import pytest

from soul_protocol.embeddings.similarity import (
    cosine_similarity,
    dot_product,
    euclidean_distance,
)


class TestCosineSimilarity:
    """Test cosine_similarity function."""

    def test_identical_vectors(self) -> None:
        vec = [1.0, 2.0, 3.0]
        assert abs(cosine_similarity(vec, vec) - 1.0) < 1e-6

    def test_opposite_vectors(self) -> None:
        a = [1.0, 0.0, 0.0]
        b = [-1.0, 0.0, 0.0]
        assert abs(cosine_similarity(a, b) - (-1.0)) < 1e-6

    def test_orthogonal_vectors(self) -> None:
        a = [1.0, 0.0]
        b = [0.0, 1.0]
        assert abs(cosine_similarity(a, b)) < 1e-6

    def test_zero_vector_a(self) -> None:
        a = [0.0, 0.0, 0.0]
        b = [1.0, 2.0, 3.0]
        assert cosine_similarity(a, b) == 0.0

    def test_zero_vector_b(self) -> None:
        a = [1.0, 2.0, 3.0]
        b = [0.0, 0.0, 0.0]
        assert cosine_similarity(a, b) == 0.0

    def test_both_zero_vectors(self) -> None:
        a = [0.0, 0.0]
        b = [0.0, 0.0]
        assert cosine_similarity(a, b) == 0.0

    def test_parallel_different_magnitude(self) -> None:
        a = [1.0, 2.0, 3.0]
        b = [2.0, 4.0, 6.0]
        assert abs(cosine_similarity(a, b) - 1.0) < 1e-6

    def test_known_value(self) -> None:
        a = [1.0, 0.0]
        b = [1.0, 1.0]
        expected = 1.0 / math.sqrt(2)
        assert abs(cosine_similarity(a, b) - expected) < 1e-6

    def test_single_dimension(self) -> None:
        assert abs(cosine_similarity([3.0], [5.0]) - 1.0) < 1e-6
        assert abs(cosine_similarity([3.0], [-5.0]) - (-1.0)) < 1e-6

    def test_empty_vectors(self) -> None:
        # Edge case: empty vectors should return 0.0
        assert cosine_similarity([], []) == 0.0


class TestEuclideanDistance:
    """Test euclidean_distance function."""

    def test_identical_vectors(self) -> None:
        vec = [1.0, 2.0, 3.0]
        assert euclidean_distance(vec, vec) == 0.0

    def test_known_distance(self) -> None:
        a = [0.0, 0.0]
        b = [3.0, 4.0]
        assert abs(euclidean_distance(a, b) - 5.0) < 1e-6

    def test_unit_distance(self) -> None:
        a = [0.0]
        b = [1.0]
        assert abs(euclidean_distance(a, b) - 1.0) < 1e-6

    def test_symmetry(self) -> None:
        a = [1.0, 2.0, 3.0]
        b = [4.0, 5.0, 6.0]
        assert abs(euclidean_distance(a, b) - euclidean_distance(b, a)) < 1e-6

    def test_zero_vectors(self) -> None:
        a = [0.0, 0.0, 0.0]
        b = [0.0, 0.0, 0.0]
        assert euclidean_distance(a, b) == 0.0

    def test_empty_vectors(self) -> None:
        assert euclidean_distance([], []) == 0.0


class TestDotProduct:
    """Test dot_product function."""

    def test_orthogonal(self) -> None:
        assert dot_product([1.0, 0.0], [0.0, 1.0]) == 0.0

    def test_known_value(self) -> None:
        a = [1.0, 2.0, 3.0]
        b = [4.0, 5.0, 6.0]
        assert dot_product(a, b) == 32.0  # 4 + 10 + 18

    def test_unit_vectors_equals_cosine(self) -> None:
        # For unit vectors, dot product == cosine similarity
        norm = math.sqrt(2)
        a = [1.0 / norm, 1.0 / norm]
        b = [1.0, 0.0]
        dp = dot_product(a, b)
        cs = cosine_similarity(a, b)
        assert abs(dp - cs) < 1e-6

    def test_empty_vectors(self) -> None:
        assert dot_product([], []) == 0.0
