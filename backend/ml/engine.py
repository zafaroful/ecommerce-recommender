"""Core recommendation logic.

Pure, deterministic functions over plain records. No network or database access
so the logic is easy to unit test. The service layer feeds these functions data
loaded through Supabase.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

MODEL_VERSION = "item-cf-v1"

INTERACTION_WEIGHTS: dict[str, float] = {
    "view": 1.0,
    "click": 2.0,
    "add_to_cart": 3.0,
    "purchase": 5.0,
    "rating": 0.0,  # rating interactions use their rating value instead
}


@dataclass(frozen=True)
class InteractionRecord:
    user_id: str
    product_id: str
    interaction_type: str
    rating: int | None = None


@dataclass(frozen=True)
class ScoredProduct:
    product_id: str
    score: float
    rank: int


def interaction_weight(record: InteractionRecord) -> float:
    if record.interaction_type == "rating":
        return float(record.rating or 0)
    return INTERACTION_WEIGHTS.get(record.interaction_type, 0.0)


def build_user_item_weights(
    interactions: list[InteractionRecord],
) -> dict[str, dict[str, float]]:
    weights: dict[str, dict[str, float]] = defaultdict(dict)
    for record in interactions:
        weight = interaction_weight(record)
        if weight <= 0:
            continue
        item_weights = weights[record.user_id]
        item_weights[record.product_id] = item_weights.get(record.product_id, 0.0) + weight
    return weights


def build_item_similarity(
    user_item_weights: dict[str, dict[str, float]],
) -> dict[str, dict[str, float]]:
    """Item-item co-occurrence similarity from the user-item weight matrix."""
    similarity: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for item_weights in user_item_weights.values():
        items = sorted(item_weights)
        for i, left in enumerate(items):
            for right in items[i + 1 :]:
                product = item_weights[left] * item_weights[right]
                similarity[left][right] += product
                similarity[right][left] += product
    return {item: dict(neighbours) for item, neighbours in similarity.items()}


def popularity_scores(
    interactions: list[InteractionRecord],
    product_category: dict[str, str] | None = None,
    preferred_category: str | None = None,
) -> dict[str, float]:
    scores: dict[str, float] = defaultdict(float)
    for record in interactions:
        weight = interaction_weight(record)
        if weight <= 0:
            continue
        category_bonus = 1.0
        if (
            product_category is not None
            and preferred_category is not None
            and product_category.get(record.product_id) == preferred_category
        ):
            category_bonus = 2.0
        scores[record.product_id] += weight * category_bonus
    return dict(scores)


def generate_recommendations(
    user_id: str,
    interactions: list[InteractionRecord],
    active_product_ids: set[str],
    product_category: dict[str, str] | None = None,
    limit: int = 10,
) -> list[ScoredProduct]:
    """Rank active catalogue products for a user.

    Collaborative filtering over the user's own history, falling back to
    popularity (with a preferred-category boost) for cold-start users. The
    result is deterministic: scores are rounded and ties break on product id.
    """
    user_item_weights = build_user_item_weights(interactions)
    user_weights = user_item_weights.get(user_id, {})

    scores: dict[str, float] = defaultdict(float)

    if user_weights:
        similarity = build_item_similarity(user_item_weights)
        for product_id, weight in user_weights.items():
            for neighbour_id, similarity_score in similarity.get(product_id, {}).items():
                if neighbour_id in user_weights:
                    continue
                scores[neighbour_id] += weight * similarity_score

    seen = set(user_weights)
    if not any(
        product_id in active_product_ids and product_id not in seen
        for product_id in scores
    ):
        preferred_category = None
        if user_weights and product_category is not None:
            category_counts: dict[str, float] = defaultdict(float)
            for product_id, weight in user_weights.items():
                category = product_category.get(product_id)
                if category:
                    category_counts[category] += weight
            if category_counts:
                preferred_category = max(sorted(category_counts), key=category_counts.get)
        scores = defaultdict(
            float,
            popularity_scores(interactions, product_category, preferred_category),
        )

    candidates = [
        (product_id, score)
        for product_id, score in scores.items()
        if product_id in active_product_ids and product_id not in seen and score > 0
    ]

    candidates.sort(key=lambda item: (-round(item[1], 6), item[0]))
    return [
        ScoredProduct(product_id=product_id, score=round(score, 6), rank=index + 1)
        for index, (product_id, score) in enumerate(candidates[:limit])
    ]