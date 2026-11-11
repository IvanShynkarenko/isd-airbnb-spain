# First run on Barcelona — Databricks (unchanged week-1 code, tag `week1-final`)

- Job `airbnb_pipeline`, run 627152171515517, 2026-11-11 22:49, parameters `cities=["barcelona"]`, `train=false`.
- Only change before the run: the Barcelona entry in `config/cities.yml` (the designed way to add a city; no code).
- Result: **succeeded** in 1 min 52 s. `etl_city` downloaded the file from Inside Airbnb itself (no manual upload),
  wrote 15 236 rows to bronze, silver and features; `train` was excluded; `score_city` used model **v1**.

`workspace.airbnb_gold.model_metrics` after the run:

| city | population | n | model MAE | baseline MAE | model_version |
|---|---|---:|---:|---:|---|
| all (Madrid+Sevilla) | ok | 5 273 | 49.64 | 66.02 | v1 |
| barcelona | ok | 2 505 | **80.65** | 85.02 | v1 |
| barcelona | all_priced | 2 575 | 122.99 | 125.48 | v1 |

Local first run (same code, scikit-learn 1.9): Barcelona ok 79.64 vs 85.02; all_priced 121.27 vs 125.48
(logs: `first_run_local_etl.log`, `first_run_local_score.log`).
