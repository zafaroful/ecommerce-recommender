from fastapi import APIRouter, Depends
from supabase import Client

from app.auth import AuthenticatedUser, get_current_user
from app.schemas import InteractionType, ProductEngagementMetric, RecommendationMetrics
from app.services.recommender import MODEL_VERSION
from app.supabase_client import get_supabase_client

router = APIRouter(tags=["metrics"])

INTERACTION_WEIGHTS: dict[InteractionType, float] = {
    "view": 1.0,
    "click": 2.0,
    "add_to_cart": 4.0,
    "purchase": 6.0,
    "rating": 0.0,
}


@router.get("/metrics/recommendations", response_model=RecommendationMetrics)
def get_recommendation_metrics(
    _user: AuthenticatedUser = Depends(get_current_user),
    client: Client = Depends(get_supabase_client),
) -> RecommendationMetrics:
    products = (
        client.table("products").select("id, name").eq("is_active", True).execute().data or []
    )
    profiles = client.table("profiles").select("id").execute().data or []
    interactions = (
        client.table("interactions")
        .select("user_id, product_id, interaction_type, rating")
        .execute()
        .data
        or []
    )
    recommendations = (
        client.table("recommendations")
        .select("user_id")
        .eq("model_version", MODEL_VERSION)
        .execute()
        .data
        or []
    )

    interactions_by_type: dict[InteractionType, int] = {
        "view": 0,
        "click": 0,
        "add_to_cart": 0,
        "purchase": 0,
        "rating": 0,
    }
    engagement_scores: dict[str, float] = {}
    users_with_interactions: set[str] = set()

    for row in interactions:
        interaction_type = row["interaction_type"]
        interactions_by_type[interaction_type] += 1
        users_with_interactions.add(row["user_id"])
        if interaction_type == "rating":
            score = float(row.get("rating") or 0)
        else:
            score = INTERACTION_WEIGHTS[interaction_type]
        engagement_scores[row["product_id"]] = engagement_scores.get(row["product_id"], 0.0) + score

    product_names = {row["id"]: row["name"] for row in products}
    top_products = [
        ProductEngagementMetric(product_id=product_id, name=product_names[product_id], score=score)
        for product_id, score in sorted(
            engagement_scores.items(), key=lambda item: (-item[1], product_names.get(item[0], ""))
        )
        if product_id in product_names
    ][:5]

    profile_ids = {row["id"] for row in profiles}
    cold_start_users = len(profile_ids - users_with_interactions)
    users_with_recommendations = {row["user_id"] for row in recommendations}

    return RecommendationMetrics(
        model_version=MODEL_VERSION,
        total_products=len(products),
        total_users=len(profiles),
        total_interactions=len(interactions),
        interactions_by_type=interactions_by_type,
        users_with_recommendations=len(users_with_recommendations),
        cold_start_users=cold_start_users,
        top_products=top_products,
    )
