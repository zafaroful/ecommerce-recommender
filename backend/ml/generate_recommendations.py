"""Offline job: generate and store recommendations for every user.

Run from the backend directory with backend credentials in the environment:

    python -m ml.generate_recommendations --confirm-write

Preview without writing:

    python -m ml.generate_recommendations --dry-run

Requires SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY. Safe to rerun: each user's
rows for the current model version are replaced atomically.

Loads the global interaction and product data once, then scores every user
against that shared context instead of re-reading the tables per user.
"""

from __future__ import annotations

import argparse

from app.services.recommender import (
    RECOMMENDATION_LIMIT,
    generate_from_context,
    load_catalog_context,
    store_recommendations,
)
from app.supabase_client import get_supabase_client
from ml.engine import MODEL_VERSION


def generate_all(
    *, dry_run: bool = False, user_id: str | None = None, limit: int | None = None
) -> int:
    client = get_supabase_client()
    interactions, active_product_ids, product_category = load_catalog_context(client)

    profiles = client.table("profiles").select("id").order("id").execute()
    user_ids = [row["id"] for row in profiles.data or []]
    if user_id:
        user_ids = [candidate for candidate in user_ids if candidate == user_id]
    if limit is not None:
        user_ids = user_ids[:limit]

    processed = 0
    for current_user_id in user_ids:
        scored = generate_from_context(
            current_user_id,
            interactions,
            active_product_ids,
            product_category,
            limit=RECOMMENDATION_LIMIT,
        )
        if dry_run:
            print(f"Dry run: {current_user_id} would receive {len(scored)} recommendation(s).")
        else:
            store_recommendations(client, current_user_id, scored)
        processed += 1
    return processed


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate stored product recommendations.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compute and report recommendations without writing rows.",
    )
    parser.add_argument(
        "--confirm-write",
        action="store_true",
        help="Required for writes; omitted in dry-run mode.",
    )
    parser.add_argument("--user-id", help="Restrict processing to one profile id.")
    parser.add_argument(
        "--limit",
        type=int,
        help="Maximum number of users to process after optional filtering.",
    )
    args = parser.parse_args()
    if not args.dry_run and not args.confirm_write:
        parser.error("writes require --confirm-write; use --dry-run to preview")
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be at least 1")
    return args


def main() -> None:
    args = _parse_args()
    processed = generate_all(dry_run=args.dry_run, user_id=args.user_id, limit=args.limit)
    action = "Previewed" if args.dry_run else "Generated"
    print(f"{action} recommendations for {processed} user(s) using {MODEL_VERSION}.")


if __name__ == "__main__":
    main()
