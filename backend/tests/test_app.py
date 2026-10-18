from fastapi.testclient import TestClient

from app.main import app


def test_openapi_schema_is_available() -> None:
    client = TestClient(app)

    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["title"] == "E-commerce Recommender API"


def test_cors_preflight_uses_explicit_methods_and_headers() -> None:
    client = TestClient(app)

    response = client.options(
        "/products",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization, Content-Type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-methods"] == "GET, POST"
    allowed_headers = response.headers["access-control-allow-headers"]
    assert "Authorization" in allowed_headers
    assert "Content-Type" in allowed_headers


def test_cors_preflight_rejects_unlisted_method() -> None:
    client = TestClient(app)

    response = client.options(
        "/products",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "DELETE",
        },
    )

    assert response.status_code == 400
