import sys

import pytest

from ml import generate_recommendations
from tests.test_routes import FakeClient


def _store() -> dict[str, list[dict]]:
    return {
        "profiles": [{"id": "u1"}, {"id": "u2"}],
        "products": [
            {
                "id": "p1",
                "category_id": "c1",
                "name": "Alpha",
                "description": None,
                "price": 10.0,
                "image_url": None,
                "is_active": True,
            }
        ],
        "interactions": [
            {
                "id": "i1",
                "user_id": "u2",
                "product_id": "p1",
                "interaction_type": "view",
                "rating": None,
                "created_at": "2026-10-18T00:00:00+00:00",
            }
        ],
        "recommendations": [],
    }


def test_generate_all_dry_run_does_not_write(monkeypatch: pytest.MonkeyPatch) -> None:
    store = _store()
    monkeypatch.setattr(generate_recommendations, "get_supabase_client", lambda: FakeClient(store))

    processed = generate_recommendations.generate_all(dry_run=True)

    assert processed == 2
    assert store["recommendations"] == []


def test_generate_all_can_limit_and_filter_user(monkeypatch: pytest.MonkeyPatch) -> None:
    store = _store()
    monkeypatch.setattr(generate_recommendations, "get_supabase_client", lambda: FakeClient(store))

    processed = generate_recommendations.generate_all(user_id="u1", limit=1)

    assert processed == 1
    assert {row["user_id"] for row in store["recommendations"]} == {"u1"}


def test_main_requires_confirmation_for_writes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["generate_recommendations"])

    with pytest.raises(SystemExit) as exc:
        generate_recommendations.main()

    assert exc.value.code == 2
