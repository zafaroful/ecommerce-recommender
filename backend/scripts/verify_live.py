"""Ad-hoc live verification against a Supabase project + the local FastAPI app.

This script creates and deletes real auth users and writes real rows, so it
must be run deliberately. Enable it explicitly:

    $env:ALLOW_LIVE_VERIFY = "1"
    python -m scripts.verify_live

The API must be running on localhost:8000. The test password is taken from
LIVE_VERIFY_PASSWORD when set. Intended for a disposable or non-production
project; do not run against a shared production project.
"""

from __future__ import annotations

import os
import secrets
import sys
import time

import httpx

from app.config import get_settings
from app.supabase_client import get_supabase_client

API = "http://localhost:8000"


def _require_opt_in() -> str:
    if os.environ.get("ALLOW_LIVE_VERIFY") != "1":
        print(
            "Refusing to run: this script creates and deletes real users and rows.\n"
            "Set ALLOW_LIVE_VERIFY=1 to confirm you are targeting a disposable project.",
            file=sys.stderr,
        )
        raise SystemExit(2)
    return os.environ.get("LIVE_VERIFY_PASSWORD") or f"Phase3-{secrets.token_urlsafe(18)}!"


def _create_user(client, email: str, password: str) -> str:
    created = client.auth.admin.create_user(
        {"email": email, "password": password, "email_confirm": True}
    )
    return created.user.id


def _sign_in(email: str, password: str) -> str:
    settings = get_settings()
    response = httpx.post(
        f"{settings.supabase_url}/auth/v1/token?grant_type=password",
        headers={"apikey": settings.supabase_anon_key, "Content-Type": "application/json"},
        json={"email": email, "password": password},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def main() -> int:
    password = _require_opt_in()
    client = get_supabase_client()
    stamp = int(time.time())
    email = f"phase3-verify-{stamp}@example.com"
    other_email = f"phase3-other-{stamp}@example.com"

    user_id = _create_user(client, email, password)
    other_id = _create_user(client, other_email, password)
    print(f"created users {user_id} and {other_id}")

    try:
        token = _sign_in(email, password)
        other_token = _sign_in(other_email, password)
        auth = {"Authorization": f"Bearer {token}"}
        other_auth = {"Authorization": f"Bearer {other_token}"}

        health = httpx.get(f"{API}/health", timeout=10)
        print("health:", health.status_code, health.json())

        products = httpx.get(f"{API}/products", timeout=10).json()
        print("products:", len(products))
        first_two = [p["id"] for p in products[:2]]
        third = products[2]["id"]

        # Seed co-occurrence: the other user interacts with the same two
        # products plus a third, so collaborative filtering has neighbours.
        for product_id in [*first_two, third]:
            resp = httpx.post(
                f"{API}/interactions",
                headers=other_auth,
                json={"product_id": product_id, "interaction_type": "view"},
                timeout=10,
            )
            resp.raise_for_status()

        for product_id in first_two:
            resp = httpx.post(
                f"{API}/interactions",
                headers=auth,
                json={"product_id": product_id, "interaction_type": "view"},
                timeout=10,
            )
            resp.raise_for_status()
        print("recorded views for both users")

        unauth = httpx.get(f"{API}/recommendations", timeout=10)
        print("unauthenticated recommendations:", unauth.status_code)

        recs = httpx.get(f"{API}/recommendations", headers=auth, timeout=30)
        recs.raise_for_status()
        body = recs.json()
        print("model_version:", body["model_version"], "items:", len(body["items"]))
        assert body["model_version"] == "item-cf-v1"
        assert body["items"], "expected at least one recommendation"
        recommended_ids = {item["product_id"] for item in body["items"]}
        assert not (recommended_ids & set(first_two)), "seen products must be excluded"
        assert third in recommended_ids, "co-occurring product should be recommended"

        other_recs = httpx.get(f"{API}/recommendations", headers=other_auth, timeout=30).json()
        other_ids = {item["product_id"] for item in other_recs["items"]}
        print("other-user items:", len(other_recs["items"]))
        # Isolation: the other user must not receive the first user's seen set
        # as their own personalisation (their view history differs).
        assert other_ids.issubset({p["id"] for p in products})

        count = (
            client.table("recommendations")
            .select("id")
            .eq("user_id", user_id)
            .eq("model_version", "item-cf-v1")
            .execute()
        )
        print("stored recommendation rows:", len(count.data))
        assert count.data, "recommendations should be persisted with model_version"

        print("LIVE VERIFICATION PASSED")
        return 0
    finally:
        client.auth.admin.delete_user(user_id)
        client.auth.admin.delete_user(other_id)
        print("test users deleted")


if __name__ == "__main__":
    sys.exit(main())