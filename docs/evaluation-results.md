# Offline evaluation results

Dataset: MovieLens 100K. Time-based split (newest 20% of each user's ratings held out). Relevant = held-out ratings >= 4. K=10.

| model                    |   Precision@10 |   Recall@10 |   NDCG@10 |   users |
|:-------------------------|---------------:|------------:|----------:|--------:|
| popularity baseline      |         0.0737 |      0.0691 |    0.0928 |     904 |
| item-cf-v1 (your engine) |         0.0949 |      0.0978 |    0.1225 |     904 |

RMSE is not reported because item-cf-v1 ranks items and does not predict ratings.
