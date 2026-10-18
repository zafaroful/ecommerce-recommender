"""Service layer bridging Supabase data and the pure recommendation engine."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from supabase import Client

from ml.engine import (
    MODEL_VERSION,
    InteractionRecord,
    ScoredProduct,
    generate_recommendations,
)

RECOMMENDATION_LIMIT = 10

# Cap the interaction history used for collaborative filtering so the request
# path stays bounded. Recent activity dominates the signal anyway.
INTERACTION_WINDOW_DAYS = 90
INTERACTION_SAMPLE_LIMIT = 5000


def _load_interactions(client: Client) -> list[InteractionRecord]:
    since = (datetime.now(UTC) - timedelta(days=INTERACTION_WINDOW_DAYS)).isoformat()
    response = (
        client.table("interactions")
        .select("user_id, product_id, interaction_type, rating")
        .gte("created_at", since)
        .order("created_at", desc=True)
        .limit(INTERACTION_SAMPLE_LIMIT)
        .execute()
    )
    return [
        InteractionRecord(
            user_id=row["user_id"],
            product_id=row["product_id"],
            interaction_type=row["interaction_type"],
            rating=row.get("rating"),
        )
        for row in response.data or []
    ]


def _load_active_products(client: Client) -> tuple[set[str], dict[str, str]]:
    response = client.table("products").select("id, category_id").eq("is_active", True).execute()
    product_ids: set[str] = set()
    product_category: dict[str, str] = {}
    for row in response.data or []:
        product_ids.add(row["id"])
        product_category[row["id"]] = row["category_id"]
    return product_ids, product_category


def generate_for_user(
    client: Client, user_id: str, limit: int = RECOMMENDATION_LIMIT
) -> list[ScoredProduct]:
    interactions = _load_interactions(client)
    active_product_ids, product_category = _load_active_products(client)
    return generate_recommendations(
        user_id=user_id,
        interactions=interactions,
        active_product_ids=active_product_ids,
        product_category=product_category,
        limit=limit,
    )


def load_catalog_context(
    client: Client,
) -> tuple[list[InteractionRecord], set[str], dict[str, str]]:
    """Load the global interaction and product data used for every user."""
    interactions = _load_interactions(client)
    active_product_ids, product_category = _load_active_products(client)
    return interactions, active_product_ids, product_category


def generate_from_context(
    user_id: str,
    interactions: list[InteractionRecord],
    active_product_ids: set[str],
    product_category: dict[str, str],
    limit: int = RECOMMENDATION_LIMIT,
) -> list[ScoredProduct]:
    """Score one user against preloaded global data (no additional queries)."""
    return generate_recommendations(
        user_id=user_id,
        interactions=interactions,
        active_product_ids=active_product_ids,
        product_category=product_category,
        limit=limit,
    )


def store_recommendations(client: Client, user_id: str, scored: list[ScoredProduct]) -> None:
    """Atomically replace a user's stored recommendations for the model version."""
    generated_at = datetime.now(UTC).isoformat()
    rows = [
        {
            "product_id": item.product_id,
            "score": item.score,
            "rank": item.rank,
            "generated_at": generated_at,
        }
        for item in scored
    ]
    client.rpc(
        "replace_recommendations",
        {
            "p_user_id": user_id,
            "p_model_version": MODEL_VERSION,
            "p_rows": rows,
        },
    ).execute()


def load_stored_recommendations(client: Client, user_id: str) -> list[dict]:
    response = (
        client.table("recommendations")
        .select("product_id, score, rank, model_version, generated_at")
        .eq("user_id", user_id)
        .eq("model_version", MODEL_VERSION)
        .order("rank")
        .execute()
    )
    return response.data or []


def load_products_by_ids(client: Client, product_ids: list[str]) -> dict[str, dict]:
    if not product_ids:
        return {}
    response = client.table("products").select("*").in_("id", product_ids).execute()
    return {row["id"]: row for row in response.data or []}