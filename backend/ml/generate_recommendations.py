"""Offline job: generate and store recommendations for every user.

Run from the backend directory with backend credentials in the environment:

    python -m ml.generate_recommendations

Requires SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY. Safe to rerun: each user's
rows for the current model version are replaced atomically.

Loads the global interaction and product data once, then scores every user
against that shared context instead of re-reading the tables per user.
"""

from __future__ import annotations

from app.services.recommender import (
    generate_from_context,
    load_catalog_context,
    store_recommendations,
)
from app.supabase_client import get_supabase_client
from ml.engine import MODEL_VERSION


def generate_all() -> int:
    client = get_supabase_client()
    interactions, active_product_ids, product_category = load_catalog_context(client)

    profiles = client.table("profiles").select("id").execute()
    user_ids = [row["id"] for row in profiles.data or []]

    processed = 0
    for user_id in user_ids:
        scored = generate_from_context(
            user_id, interactions, active_product_ids, product_category
        )
        store_recommendations(client, user_id, scored)
        processed += 1
    return processed


def main() -> None:
    processed = generate_all()
    print(f"Generated recommendations for {processed} user(s) using {MODEL_VERSION}.")


if __name__ == "__main__":
    main()