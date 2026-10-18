from app.services import recommender
from tests.test_routes import FakeClient


def _store() -> dict[str, list[dict]]:
    return {
        "products": [
            {
                "id": "p1",
                "category_id": "c1",
                "name": "Alpha",
                "description": None,
                "price": 10.0,
                "image_url": None,
                "is_active": True,
            },
            {
                "id": "p2",
                "category_id": "c1",
                "name": "Beta",
                "description": None,
                "price": 20.0,
                "image_url": None,
                "is_active": True,
            },
        ],
        "interactions": [
            {
                "id": "x1",
                "user_id": "u2",
                "product_id": "p1",
                "interaction_type": "view",
                "rating": None,
            },
            {
                "id": "x2",
                "user_id": "u2",
                "product_id": "p2",
                "interaction_type": "view",
                "rating": None,
            },
        ],
        "recommendations": [],
    }


def test_load_catalog_context_returns_three_parts() -> None:
    client = FakeClient(_store())
    interactions, active_product_ids, product_category = recommender.load_catalog_context(client)

    assert len(interactions) == 2
    assert active_product_ids == {"p1", "p2"}
    assert product_category == {"p1": "c1", "p2": "c1"}


def test_generate_from_context_scores_without_extra_queries() -> None:
    client = FakeClient(_store())
    interactions, active_product_ids, product_category = recommender.load_catalog_context(client)

    results = recommender.generate_from_context(
        "u1", interactions, active_product_ids, product_category
    )
    assert [item.product_id for item in results] == ["p1", "p2"]


def test_store_recommendations_uses_atomic_rpc() -> None:
    client = FakeClient(_store())
    interactions, active_product_ids, product_category = recommender.load_catalog_context(client)
    # u1 has no interactions, so it receives popularity/CF recommendations.
    scored = recommender.generate_from_context(
        "u1", interactions, active_product_ids, product_category
    )
    assert scored

    recommender.store_recommendations(client, "u1", scored)
    stored = client.store["recommendations"]
    assert stored
    assert all(row["user_id"] == "u1" for row in stored)
    assert all(row["model_version"] == recommender.MODEL_VERSION for row in stored)

    # A second replace must fully replace the prior set, not append.
    recommender.store_recommendations(client, "u1", scored[:1])
    stored_again = client.store["recommendations"]
    assert len(stored_again) == 1
    assert stored_again[0]["rank"] == 1