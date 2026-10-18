from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from supabase import Client

from app.auth import AuthenticatedUser, get_current_user
from app.schemas import (
    DEFAULT_PAGE_LIMIT,
    INTERACTION_FIELDS,
    MAX_PAGE_LIMIT,
    Interaction,
    InteractionCreate,
    InteractionListItem,
)
from app.supabase_client import get_supabase_client

router = APIRouter(tags=["interactions"])


@router.post("/interactions", response_model=Interaction, status_code=status.HTTP_201_CREATED)
def create_interaction(
    payload: InteractionCreate,
    user: AuthenticatedUser = Depends(get_current_user),
    client: Client = Depends(get_supabase_client),
) -> Interaction:
    if payload.interaction_type == "rating" and payload.rating is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="A rating value is required for rating interactions.",
        )
    if payload.interaction_type != "rating" and payload.rating is not None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="A rating value is only allowed for rating interactions.",
        )

    product = (
        client.table("products")
        .select("id")
        .eq("id", payload.product_id)
        .eq("is_active", True)
        .maybe_single()
        .execute()
    )
    if not product.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    row = {
        "user_id": user.id,
        "product_id": payload.product_id,
        "interaction_type": payload.interaction_type,
        "rating": payload.rating,
        "created_at": datetime.now(UTC).isoformat(),
    }
    response = client.table("interactions").insert(row).execute()
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record interaction.",
        )
    return Interaction(**response.data[0])


@router.get("/interactions", response_model=list[InteractionListItem])
def list_interactions(
    limit: int = Query(default=DEFAULT_PAGE_LIMIT, ge=1),
    offset: int = Query(default=0, ge=0),
    user: AuthenticatedUser = Depends(get_current_user),
    client: Client = Depends(get_supabase_client),
) -> list[InteractionListItem]:
    safe_limit = min(limit, MAX_PAGE_LIMIT)
    response = (
        client.table("interactions")
        .select(INTERACTION_FIELDS)
        .eq("user_id", user.id)
        .order("created_at", desc=True)
        .range(offset, offset + safe_limit - 1)
        .execute()
    )
    return [InteractionListItem(**row) for row in response.data or []]
