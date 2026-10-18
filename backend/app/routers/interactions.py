from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from app.auth import AuthenticatedUser, get_current_user
from app.schemas import Interaction, InteractionCreate
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


@router.get("/interactions", response_model=list[Interaction])
def list_interactions(
    user: AuthenticatedUser = Depends(get_current_user),
    client: Client = Depends(get_supabase_client),
) -> list[Interaction]:
    response = (
        client.table("interactions")
        .select("*")
        .eq("user_id", user.id)
        .order("created_at", desc=True)
        .execute()
    )
    return [Interaction(**row) for row in response.data or []]