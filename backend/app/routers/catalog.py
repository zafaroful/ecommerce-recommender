from fastapi import APIRouter, Depends, HTTPException, Query, status
from supabase import Client

from app.schemas import (
    DEFAULT_PAGE_LIMIT,
    MAX_PAGE_LIMIT,
    PRODUCT_FIELDS,
    Category,
    Product,
    ProductListItem,
)
from app.supabase_client import get_supabase_client

router = APIRouter(tags=["catalog"])


@router.get("/categories", response_model=list[Category])
def list_categories(client: Client = Depends(get_supabase_client)) -> list[Category]:
    response = client.table("categories").select("*").order("name").execute()
    return [Category(**row) for row in response.data or []]


@router.get("/products", response_model=list[ProductListItem])
def list_products(
    category_id: str | None = None,
    limit: int = Query(default=DEFAULT_PAGE_LIMIT, ge=1),
    offset: int = Query(default=0, ge=0),
    client: Client = Depends(get_supabase_client),
) -> list[ProductListItem]:
    safe_limit = min(limit, MAX_PAGE_LIMIT)
    query = client.table("products").select(PRODUCT_FIELDS).eq("is_active", True)
    if category_id:
        query = query.eq("category_id", category_id)
    response = query.order("name").range(offset, offset + safe_limit - 1).execute()
    return [ProductListItem(**row) for row in response.data or []]


@router.get("/products/{product_id}", response_model=Product)
def get_product(product_id: str, client: Client = Depends(get_supabase_client)) -> Product:
    response = (
        client.table("products")
        .select(PRODUCT_FIELDS)
        .eq("id", product_id)
        .maybe_single()
        .execute()
    )
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    return Product(**response.data)
