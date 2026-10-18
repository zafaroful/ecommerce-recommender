from typing import Literal

from pydantic import BaseModel, Field

InteractionType = Literal["view", "click", "add_to_cart", "purchase", "rating"]

DEFAULT_PAGE_LIMIT = 25
MAX_PAGE_LIMIT = 100
PRODUCT_FIELDS = "id, category_id, name, description, price, image_url, is_active"
INTERACTION_FIELDS = "id, user_id, product_id, interaction_type, rating, created_at"


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


class ProductListItem(BaseModel):
    id: str
    category_id: str
    name: str
    description: str | None = None
    price: float
    image_url: str | None = None


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


class InteractionListItem(BaseModel):
    id: str
    product_id: str
    interaction_type: InteractionType
    rating: int | None = None
    created_at: str


class Recommendation(BaseModel):
    product_id: str
    score: float
    rank: int
    model_version: str
    reason: str
    product: Product | None = None


class RecommendationList(BaseModel):
    model_version: str
    generated_at: str | None = None
    items: list[Recommendation]
