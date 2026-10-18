from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from app.schemas import Category, Product
from app.supabase_client import get_supabase_client

router = APIRouter(tags=["catalog"])


@router.get("/categories", response_model=list[Category])
def list_categories(client: Client = Depends(get_supabase_client)) -> list[Category]:
    response = client.table("categories").select("*").order("name").execute()
    return [Category(**row) for row in response.data or []]


@router.get("/products", response_model=list[Product])
def list_products(
    category_id: str | None = None,
    client: Client = Depends(get_supabase_client),
) -> list[Product]:
    query = client.table("products").select("*").eq("is_active", True)
    if category_id:
        query = query.eq("category_id", category_id)
    response = query.order("name").execute()
    return [Product(**row) for row in response.data or []]


@router.get("/products/{product_id}", response_model=Product)
def get_product(product_id: str, client: Client = Depends(get_supabase_client)) -> Product:
    response = client.table("products").select("*").eq("id", product_id).maybe_single().execute()
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    return Product(**response.data)