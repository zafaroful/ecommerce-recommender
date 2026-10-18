from typing import Literal

from pydantic import BaseModel, Field

InteractionType = Literal["view", "click", "add_to_cart", "purchase", "rating"]


class Category(BaseModel):
    id: str
    name: str
    slug: str
    description: str | None = None


class Product(BaseModel):
    id: str
    category_id: str
    name: str
    description: str | None = None
    price: float
    image_url: str | None = None
    is_active: bool


class InteractionCreate(BaseModel):
    product_id: str
    interaction_type: InteractionType
    rating: int | None = Field(default=None, ge=1, le=5)


class Interaction(BaseModel):
    id: str
    user_id: str
    product_id: str
    interaction_type: InteractionType
    rating: int | None = None
    created_at: str


class Recommendation(BaseModel):
    product_id: str
    score: float
    rank: int
    model_version: str
    product: Product | None = None


class RecommendationList(BaseModel):
    model_version: str
    generated_at: str | None = None
    items: list[Recommendation]