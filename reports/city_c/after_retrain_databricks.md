# Barcelona after the model change — Databricks

Job `airbnb_pipeline`, run 996010984346098, 2026-11-11 22:59–23:07, parameters
`cities=["madrid","sevilla","barcelona"]`, `train=true`, `train_cities=["madrid","sevilla","barcelona"]`.
Model **v2** (HGB chosen by CV again), registered as `price_model@prod`. Includes pipeline fix `2c136b7`.

| city | population | n | model MAE | baseline MAE (3-city medians) | model_version |
|---|---|---:|---:|---:|---|
| all | ok | 7 778 | 49.34 | 71.63 | v2 |
| barcelona | ok | 2 505 | **47.85** | 82.74 | v2 |
| madrid | ok | 3 763 | 50.15 | 66.85 | v2 |
| sevilla | ok | 1 510 | 49.80 | 65.11 | v2 |
| barcelona | all_priced | 2 575 | 81.83 | 123.36 | v2 |
| madrid | all_priced | 3 794 | 66.14 | 83.09 | v2 |
| sevilla | all_priced | 1 526 | 75.44 | 90.81 | v2 |

`unseen_neighbourhood_share` is 0 for every city after the retrain.
