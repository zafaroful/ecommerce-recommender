from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from ml.engine import (
    InteractionRecord,
    build_item_similarity,
    build_user_item_weights,
    popularity_scores,
)
from ml.metrics import ndcg_at_k, precision_at_k, recall_at_k

DEFAULT_DATA = Path(__file__).parent / "data" / "ml-100k" / "u.data"
DEFAULT_OUTPUT = Path(__file__).resolve().parents[2] / "docs" / "evaluation-results.md"
POSITIVE_RATING = 4  # ratings >= 4 count as "relevant" in the test set


def load_movielens(path: Path, min_interactions: int = 5) -> pd.DataFrame:
    df = pd.read_csv(path, sep="\t", names=["user_id", "product_id", "rating", "ts"])
    size = df.groupby("user_id")["product_id"].transform("size")
    return df[size >= min_interactions].reset_index(drop=True)


def split_by_time(df: pd.DataFrame, test_fraction: float = 0.2):
    df = df.sort_values(["user_id", "ts", "product_id"]).reset_index(drop=True)
    size = df.groupby("user_id")["product_id"].transform("size")
    position = df.groupby("user_id").cumcount()
    n_test = np.maximum(1, (size * test_fraction).astype(int))
    is_test = position >= (size - n_test)
    return df[~is_test], df[is_test]


class Popularity:
    """Baseline: most-liked items in training, excluding what the user has seen."""

    name = "popularity baseline"

    def fit(self, train: pd.DataFrame) -> "Popularity":
        liked = train[train["rating"] >= POSITIVE_RATING]
        self.ranked = liked["product_id"].value_counts().index.tolist()
        self.seen = train.groupby("user_id")["product_id"].agg(set).to_dict()
        return self

    def recommend(self, user_id: int, k: int) -> list[int]:
        seen = self.seen.get(user_id, set())
        return [i for i in self.ranked if i not in seen][:k]


class EngineCF:
    """Wraps ml.engine (item-cf-v1). Builds similarity once, then scores per user
    using the same logic as engine.generate_recommendations."""

    name = "item-cf-v1 (your engine)"

    def fit(self, train: pd.DataFrame) -> "EngineCF":
        records = [
            InteractionRecord(str(u), str(p), "rating", int(r))
            for u, p, r in zip(train["user_id"], train["product_id"], train["rating"])
        ]
        self.user_weights = build_user_item_weights(records)
        self.similarity = build_item_similarity(self.user_weights)
        self.popularity = popularity_scores(records)
        self.active = set(train["product_id"].astype(str))
        return self

    def recommend(self, user_id: int, k: int) -> list[int]:
        weights = self.user_weights.get(str(user_id), {})
        seen = set(weights)
        scores: dict[str, float] = {}
        for product_id, weight in weights.items():
            for neighbour, sim in self.similarity.get(product_id, {}).items():
                if neighbour in weights:
                    continue
                scores[neighbour] = scores.get(neighbour, 0.0) + weight * sim

        if not any(p in self.active and p not in seen for p in scores):
            scores = dict(self.popularity)  # cold-start fallback, same as engine

        candidates = [
            (p, s) for p, s in scores.items()
            if p in self.active and p not in seen and s > 0
        ]
        candidates.sort(key=lambda item: (-round(item[1], 6), item[0]))
        return [int(p) for p, _ in candidates[:k]]


def evaluate(model, test: pd.DataFrame, k: int, max_users: int | None) -> dict:
    positives = test[test["rating"] >= POSITIVE_RATING]
    relevant_by_user = positives.groupby("user_id")["product_id"].agg(set)
    if max_users:
        relevant_by_user = relevant_by_user.iloc[:max_users]
    rows = []
    for user_id, relevant in relevant_by_user.items():
        recs = model.recommend(user_id, k)
        rows.append((
            precision_at_k(recs, relevant, k),
            recall_at_k(recs, relevant, k),
            ndcg_at_k(recs, relevant, k),
        ))
    p, r, n = np.mean(rows, axis=0)
    return {
        "model": model.name,
        f"Precision@{k}": p,
        f"Recall@{k}": r,
        f"NDCG@{k}": n,
        "users": len(rows),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline recommender evaluation")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--k", type=int, default=10)
    parser.add_argument("--max-users", type=int, default=None, help="quick test on first N users")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    df = load_movielens(args.data)
    train, test = split_by_time(df)
    print(f"users={df['user_id'].nunique()} train={len(train)} test={len(test)}")

    results = []
    for model in (Popularity(), EngineCF()):
        print(f"Fitting and evaluating: {model.name} ...")
        results.append(evaluate(model.fit(train), test, args.k, args.max_users))

    table = pd.DataFrame(results).round(4)
    print(table.to_string(index=False))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "# Offline evaluation results\n\n"
        f"Dataset: MovieLens 100K. Time-based split (newest 20% of each user's ratings held out). "
        f"Relevant = held-out ratings >= {POSITIVE_RATING}. K={args.k}.\n\n"
        + table.to_markdown(index=False)
        + "\n\nRMSE is not reported because item-cf-v1 ranks items and does not predict ratings.\n",
        encoding="utf-8",
    )
    print(f"Saved to {args.output}")


if __name__ == "__main__":
    main()