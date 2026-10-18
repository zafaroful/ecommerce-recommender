from fastapi import APIRouter, Depends, Query
from supabase import Client

from app.auth import AuthenticatedUser, get_current_user
from app.schemas import Product, Recommendation, RecommendationList
from app.services import recommender
from app.supabase_client import get_supabase_client

router = APIRouter(tags=["recommendations"])


@router.get("/recommendations", response_model=RecommendationList)
def get_recommendations(
    limit: int = Query(default=recommender.RECOMMENDATION_LIMIT, ge=1, le=50),
    refresh: bool = Query(default=False),
    user: AuthenticatedUser = Depends(get_current_user),
    client: Client = Depends(get_supabase_client),
) -> RecommendationList:
    stored = recommender.load_stored_recommendations(client, user.id)

    if refresh or not stored:
        scored = recommender.generate_for_user(client, user.id, limit=limit)
        recommender.store_recommendations(client, user.id, scored)
        stored = recommender.load_stored_recommendations(client, user.id)

    stored = stored[:limit]
    product_ids = [row["product_id"] for row in stored]
    products = recommender.load_products_by_ids(
        client, product_ids
    )
    reasons = recommender.recommendation_reasons(client, user.id, product_ids)

    items = [
        Recommendation(
            product_id=row["product_id"],
            score=row["score"],
            rank=row["rank"],
            model_version=row["model_version"],
            reason=reasons.get(row["product_id"], "Recommended for you."),
            product=Product(**products[row["product_id"]])
            if row["product_id"] in products
            else None,
        )
        for row in stored
    ]

    model_version = stored[0]["model_version"] if stored else recommender.MODEL_VERSION
    generated_at = stored[0]["generated_at"] if stored else None
    return RecommendationList(
        model_version=model_version,
        generated_at=generated_at,
        items=items,
    )
