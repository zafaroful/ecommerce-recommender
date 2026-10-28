import math

import pytest

from ml.metrics import ndcg_at_k, precision_at_k, recall_at_k

RECOMMENDED = [1, 2, 3, 4, 5]
RELEVANT = {2, 5, 9}


def test_precision():
    assert precision_at_k(RECOMMENDED, RELEVANT, 5) == pytest.approx(2 / 5)


def test_recall():
    assert recall_at_k(RECOMMENDED, RELEVANT, 5) == pytest.approx(2 / 3)


def test_ndcg():
    dcg = 1 / math.log2(3) + 1 / math.log2(6)  # hits at ranks 2 and 5
    ideal = 1 + 1 / math.log2(3) + 1 / math.log2(4)  # 3 relevant items
    assert ndcg_at_k(RECOMMENDED, RELEVANT, 5) == pytest.approx(dcg / ideal)


def test_empty_relevant_is_zero():
    assert recall_at_k(RECOMMENDED, set(), 5) == 0.0
    assert ndcg_at_k(RECOMMENDED, set(), 5) == 0.0