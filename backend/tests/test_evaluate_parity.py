import pandas as pd

from ml.engine import InteractionRecord, generate_recommendations
from ml.evaluate import EngineCF


def test_wrapper_matches_engine():
    rows = [
        (1, 10, 5), (1, 11, 4), (2, 10, 5), (2, 12, 4),
        (3, 11, 5), (3, 12, 5), (3, 13, 3), (4, 13, 4),
    ]
    train = pd.DataFrame(rows, columns=["user_id", "product_id", "rating"])
    model = EngineCF().fit(train)

    records = [InteractionRecord(str(u), str(p), "rating", r) for u, p, r in rows]
    active = {str(p) for p in train["product_id"]}
    for user in (1, 2, 3, 4):
        expected = [
            int(s.product_id)
            for s in generate_recommendations(str(user), records, active, limit=5)
        ]
        assert model.recommend(user, 5) == expected