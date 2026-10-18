from typing import Any

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from app.auth import AuthenticatedUser, get_current_user
from app.main import app
from app.supabase_client import get_supabase_client

PRODUCTS = [
    {
        "id": "p1",
        "category_id": "c1",
        "name": "Alpha",
        "description": "First",
        "price": 10.0,
        "image_url": None,
        "is_active": True,
    },
    {
        "id": "p2",
        "category_id": "c1",
        "name": "Beta",
        "description": "Second",
        "price": 20.0,
        "image_url": None,
        "is_active": True,
    },
]


class FakeResponse:
    def __init__(self, data: Any) -> None:
        self.data = data


class FakeQuery:
    def __init__(self, table: str, store: dict[str, list[dict]]) -> None:
        self.table = table
        self.store = store
        self._filters: dict[str, Any] = {}
        self._in: tuple[str, list[str]] | None = None
        self._order: tuple[str, bool] | None = None
        self._range: tuple[int, int] | None = None
        self._single = False

    def select(self, *_args: Any, **_kwargs: Any) -> "FakeQuery":
        return self

    def eq(self, column: str, value: Any) -> "FakeQuery":
        self._filters[column] = value
        return self

    def in_(self, column: str, values: list[str]) -> "FakeQuery":
        self._in = (column, values)
        return self

    def gte(self, *_args: Any, **_kwargs: Any) -> "FakeQuery":
        return self

    def limit(self, count: int) -> "FakeQuery":
        self._range = (0, count - 1)
        return self

    def order(self, column: str, desc: bool = False, **_kwargs: Any) -> "FakeQuery":
        self._order = (column, desc)
        return self

    def range(self, start: int, end: int) -> "FakeQuery":
        self._range = (start, end)
        return self

    def maybe_single(self) -> "FakeQuery":
        self._single = True
        return self

    def insert(self, rows: Any) -> "FakeQuery":
        records = rows if isinstance(rows, list) else [rows]
        self._inserted = []
        for record in records:
            stored = dict(record)
            stored.setdefault("id", f"i{len(self.store.get(self.table, [])) + 1}")
            self.store.setdefault(self.table, []).append(stored)
            self._inserted.append(stored)
        return self

    def delete(self) -> "FakeQuery":
        return self

    def execute(self) -> FakeResponse:
        if self.table == "interactions" and hasattr(self, "_inserted"):
            return FakeResponse(self._inserted)
        rows = list(self.store.get(self.table, []))
        for column, value in self._filters.items():
            rows = [r for r in rows if r.get(column) == value]
        if self._in:
            column, values = self._in
            rows = [r for r in rows if r.get(column) in values]
        if self._order:
            column, desc = self._order
            rows = sorted(rows, key=lambda r: r.get(column) or "", reverse=desc)
        if self._range:
            start, end = self._range
            rows = rows[start : end + 1]
        if self._single:
            return FakeResponse(rows[0] if rows else None)
        return FakeResponse(rows)


class FakeClient:
    def __init__(self, store: dict[str, list[dict]]) -> None:
        self.store = store

    def table(self, name: str) -> FakeQuery:
        return FakeQuery(name, self.store)

    def rpc(self, name: str, params: dict) -> "FakeRpc":
        return FakeRpc(name, params, self.store)


class FakeRpc:
    """Emulates the atomic replace_recommendations database function."""

    def __init__(self, name: str, params: dict, store: dict[str, list[dict]]) -> None:
        self.name = name
        self.params = params
        self.store = store

    def execute(self) -> FakeResponse:
        user_id = self.params["p_user_id"]
        model_version = self.params["p_model_version"]
        rows = self.params["p_rows"]
        existing = self.store.get("recommendations", [])
        remaining = [
            r
            for r in existing
            if not (r.get("user_id") == user_id and r.get("model_version") == model_version)
        ]
        for row in rows:
            remaining.append(
                {
                    "id": f"r{len(remaining) + 1}",
                    "user_id": user_id,
                    "model_version": model_version,
                    **row,
                }
            )
        self.store["recommendations"] = remaining
        return FakeResponse(None)


@pytest.fixture
def client_and_store() -> tuple[TestClient, dict[str, list[dict]]]:
    store = {"products": [dict(p) for p in PRODUCTS], "categories": [], "interactions": []}
    fake = FakeClient(store)
    app.dependency_overrides[get_supabase_client] = lambda: fake
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        id="u1", email="u@example.com"
    )
    yield TestClient(app), store
    app.dependency_overrides.clear()


def test_health(client_and_store: tuple[TestClient, dict]) -> None:
    client, _ = client_and_store
    assert client.get("/health").json() == {"status": "ok"}


def test_list_products(client_and_store: tuple[TestClient, dict]) -> None:
    client, _ = client_and_store
    response = client.get("/products")
    assert response.status_code == 200
    assert [p["id"] for p in response.json()] == ["p1", "p2"]
    assert "is_active" not in response.json()[0]


def test_list_products_paginates_and_clamps_limit(
    client_and_store: tuple[TestClient, dict],
) -> None:
    client, store = client_and_store
    store["products"] = [
        {
            "id": f"p{i:03}",
            "category_id": "c1",
            "name": f"Product {i:03}",
            "description": None,
            "price": float(i),
            "image_url": None,
            "is_active": True,
        }
        for i in range(130)
    ]

    assert len(client.get("/products").json()) == 25
    assert [p["id"] for p in client.get("/products?limit=2&offset=3").json()] == [
        "p003",
        "p004",
    ]
    assert len(client.get("/products?limit=500").json()) == 100
    assert client.get("/products?limit=10&offset=500").json() == []


def test_get_product_missing_returns_404(client_and_store: tuple[TestClient, dict]) -> None:
    client, _ = client_and_store
    assert client.get("/products/missing").status_code == 404


def test_create_interaction_requires_rating_for_rating_type(
    client_and_store: tuple[TestClient, dict],
) -> None:
    client, _ = client_and_store
    response = client.post("/interactions", json={"product_id": "p1", "interaction_type": "rating"})
    assert response.status_code == 422


def test_create_interaction_rejects_rating_on_view(
    client_and_store: tuple[TestClient, dict],
) -> None:
    client, _ = client_and_store
    response = client.post(
        "/interactions", json={"product_id": "p1", "interaction_type": "view", "rating": 4}
    )
    assert response.status_code == 422


def test_create_interaction_ok(client_and_store: tuple[TestClient, dict]) -> None:
    client, store = client_and_store
    response = client.post("/interactions", json={"product_id": "p1", "interaction_type": "view"})
    assert response.status_code == 201
    assert response.json()["user_id"] == "u1"
    assert store["interactions"][0]["product_id"] == "p1"


def test_list_interactions_paginates_and_projects_fields(
    client_and_store: tuple[TestClient, dict],
) -> None:
    client, store = client_and_store
    store["interactions"] = [
        {
            "id": f"i{i}",
            "user_id": "u1",
            "product_id": "p1",
            "interaction_type": "view",
            "rating": None,
            "created_at": f"2026-10-18T00:00:{i:02d}+00:00",
        }
        for i in range(6)
    ]

    response = client.get("/interactions?limit=2&offset=1")
    assert response.status_code == 200
    body = response.json()
    assert [row["id"] for row in body] == ["i4", "i3"]
    assert "user_id" not in body[0]
    assert client.get("/interactions?limit=2&offset=99").json() == []


def test_create_interaction_missing_product(client_and_store: tuple[TestClient, dict]) -> None:
    client, _ = client_and_store
    response = client.post(
        "/interactions", json={"product_id": "nope", "interaction_type": "view"}
    )
    assert response.status_code == 404


def test_recommendations_requires_auth() -> None:
    app.dependency_overrides.clear()
    client = TestClient(app)
    response = client.get("/recommendations")
    assert response.status_code == 401


def test_recommendations_persist_and_return(client_and_store: tuple[TestClient, dict]) -> None:
    client, store = client_and_store
    store["interactions"] = [
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
    ]
    store["recommendations"] = []
    response = client.get("/recommendations")
    assert response.status_code == 200
    body = response.json()
    assert body["model_version"] == "item-cf-v1"
    assert body["items"]
    assert store["recommendations"]


def test_interaction_to_recommendations_flow_through_api(
    client_and_store: tuple[TestClient, dict],
) -> None:
    client, store = client_and_store
    store["interactions"] = [
        {
            "id": "x1",
            "user_id": "u2",
            "product_id": "p1",
            "interaction_type": "view",
            "rating": None,
            "created_at": "2026-10-18T00:00:00+00:00",
        },
        {
            "id": "x2",
            "user_id": "u2",
            "product_id": "p2",
            "interaction_type": "view",
            "rating": None,
            "created_at": "2026-10-18T00:00:01+00:00",
        },
    ]
    store["recommendations"] = []

    interaction = client.post(
        "/interactions", json={"product_id": "p1", "interaction_type": "view"}
    )
    assert interaction.status_code == 201

    recommendations = client.get("/recommendations?refresh=true&limit=5")
    assert recommendations.status_code == 200
    items = recommendations.json()["items"]
    assert [item["product_id"] for item in items] == ["p2"]
    assert store["recommendations"][0]["user_id"] == "u1"


def test_recommendations_bad_token_is_rejected() -> None:
    app.dependency_overrides.clear()
    client = TestClient(app)

    def _raise() -> AuthenticatedUser:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required."
        )

    app.dependency_overrides[get_current_user] = _raise
    app.dependency_overrides[get_supabase_client] = lambda: FakeClient({})
    try:
        assert client.get("/recommendations").status_code == 401
    finally:
        app.dependency_overrides.clear()
