from ml.engine import (
    InteractionRecord,
    build_item_similarity,
    build_user_item_weights,
    generate_recommendations,
    interaction_weight,
)


def test_interaction_weight_uses_rating_value() -> None:
    assert interaction_weight(InteractionRecord("u1", "p1", "rating", 4)) == 4.0
    assert interaction_weight(InteractionRecord("u1", "p1", "purchase")) == 5.0


def test_build_user_item_weights_aggregates_repeats() -> None:
    interactions = [
        InteractionRecord("u1", "p1", "view"),
        InteractionRecord("u1", "p1", "click"),
        InteractionRecord("u1", "p2", "rating", 5),
    ]
    weights = build_user_item_weights(interactions)
    assert weights["u1"]["p1"] == 3.0
    assert weights["u1"]["p2"] == 5.0


def test_build_item_similarity_is_symmetric() -> None:
    weights = {"u1": {"p1": 2.0, "p2": 3.0}}
    similarity = build_item_similarity(weights)
    assert similarity["p1"]["p2"] == 6.0
    assert similarity["p2"]["p1"] == 6.0


def test_collaborative_filtering_recommends_similar_items() -> None:
    interactions = [
        InteractionRecord("u1", "p1", "purchase"),
        InteractionRecord("u2", "p1", "view"),
        InteractionRecord("u2", "p2", "view"),
    ]
    results = generate_recommendations(
        user_id="u1",
        interactions=interactions,
        active_product_ids={"p1", "p2", "p3"},
    )
    assert [item.product_id for item in results] == ["p2"]
    assert results[0].rank == 1


def test_excludes_already_seen_products() -> None:
    interactions = [
        InteractionRecord("u1", "p1", "view"),
        InteractionRecord("u2", "p1", "view"),
        InteractionRecord("u2", "p2", "view"),
    ]
    results = generate_recommendations(
        user_id="u1",
        interactions=interactions,
        active_product_ids={"p1", "p2"},
    )
    assert [item.product_id for item in results] == ["p2"]


def test_user_without_cooccurrence_falls_back_to_popularity() -> None:
    interactions = [
        InteractionRecord("u1", "p1", "view"),
        InteractionRecord("u2", "p2", "purchase"),
    ]
    results = generate_recommendations(
        user_id="u1",
        interactions=interactions,
        active_product_ids={"p1", "p2", "p3"},
    )
    # u1 has history but no co-occurrence; p2 (only seen by u2) is popular.
    assert [item.product_id for item in results] == ["p2"]


def test_cold_start_falls_back_to_popularity() -> None:
    interactions = [
        InteractionRecord("u2", "p2", "purchase"),
        InteractionRecord("u3", "p2", "view"),
        InteractionRecord("u2", "p1", "view"),
    ]
    results = generate_recommendations(
        user_id="new-user",
        interactions=interactions,
        active_product_ids={"p1", "p2"},
    )
    assert [item.product_id for item in results] == ["p2", "p1"]


def test_cold_start_prefers_top_category() -> None:
    interactions = [
        InteractionRecord("u1", "p1", "view"),
        InteractionRecord("u2", "p2", "view"),
        InteractionRecord("u2", "p3", "view"),
    ]
    results = generate_recommendations(
        user_id="u1",
        interactions=interactions,
        active_product_ids={"p1", "p2", "p3"},
        product_category={"p1": "audio", "p2": "audio", "p3": "home"},
    )
    # p1's category (audio) boosts p2 over p3.
    assert [item.product_id for item in results][0] == "p2"


def test_results_are_deterministic_with_ties() -> None:
    interactions = [InteractionRecord("u2", "p1", "view"), InteractionRecord("u2", "p2", "view")]
    first = generate_recommendations(
        user_id="u1", interactions=interactions, active_product_ids={"p1", "p2"}
    )
    second = generate_recommendations(
        user_id="u1", interactions=interactions, active_product_ids={"p1", "p2"}
    )
    assert [i.product_id for i in first] == [i.product_id for i in second] == ["p1", "p2"]
    assert [i.rank for i in first] == [1, 2]


def test_limit_is_respected() -> None:
    interactions = [
        InteractionRecord("u2", "p1", "view"),
        InteractionRecord("u2", "p2", "view"),
        InteractionRecord("u2", "p3", "view"),
    ]
    results = generate_recommendations(
        user_id="u1",
        interactions=interactions,
        active_product_ids={"p1", "p2", "p3"},
        limit=2,
    )
    assert len(results) == 2