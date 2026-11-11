# Team ISD — Airbnb Spain lakehouse, price model and new-city transfer

Group Assignment 2. A short-term-rental analytics start-up builds a lakehouse over Inside Airbnb data for two client
cities, a price model, an AI/BI dashboard and a Genie Agent — then a third client city arrives.

| | |
|---|---|
| Region | **Spain** (EUR) |
| City A (training) | **Madrid** — snapshot **2026-09-17** |
| City B (training) | **Sevilla** — snapshot **2026-09-25** |
| City C (new client) | **Barcelona** — snapshot **2026-09-17** (opened only after tag `week1-final`) |
| Why Barcelona | _(edit to match the sentence posted in Teams)_ Spain's other big Airbnb market, with strict licensing and a different neighbourhood structure: the hardest realistic test of whether a Madrid+Sevilla pipeline is a product or a prototype. |
| Data | [Inside Airbnb](https://insideairbnb.com/get-the-data/) `listings.csv.gz` (CC BY 4.0) |
| Platform | Databricks Free Edition (serverless, Unity Catalog `workspace`), zero cost |

## Results (week 1, test set = 20% of listings per city)

| | model MAE | baseline MAE | improvement |
|---|---:|---:|---:|
| Madrid | 49.9 EUR | 67.1 EUR | −26% |
| Sevilla | 49.0 EUR | 63.4 EUR | −23% |
| both | 49.6 EUR | 66.0 EUR | −25% |

Listings priced 10–1000 EUR/night (99% of priced listings). Including outliers, the MAE is 68.4 EUR vs 85.1 EUR
for the baseline. Numbers from the Databricks run (model v1). Details: [reports/week1_metrics.md](reports/week1_metrics.md).

## City C: Barcelona

| test MAE, EUR (price 10–1000) | |
|---|---:|
| Baseline on Barcelona (Madrid + Sevilla medians) | 85.02 |
| Model on Madrid + Sevilla (v1) | 49.64 |
| Model on Barcelona, first run (v1, unchanged) | 80.65 |
| Model on Barcelona after retraining with Barcelona's training split (v2) | 47.85 |

The unchanged pipeline ran on Barcelona without a failure; the model did not transfer (a higher price level, a third of
listings are mid-term stays, every neighbourhood unseen). Full story and the list of changes:
[reports/city_c.md](reports/city_c.md).

## Repository

| path | what |
|---|---|
| [notebooks/eda_madrid_sevilla.ipynb](notebooks/eda_madrid_sevilla.ipynb) | Exploratory analysis and leakage review (executed, with outputs) |
| [docs/architecture.md](docs/architecture.md) | Medallion architecture diagram and description |
| [config/cities.yml](config/cities.yml) | Everything city-specific. Adding a city = adding an entry |
| [src/airbnb/](src/airbnb/) | Pipeline logic: `ingest`, `bronze`, `silver`, `gold`, `features`, `baseline`, `model`, `modeling_job` |
| [notebooks/00_setup_job.py](notebooks/00_setup_job.py) | Creates or updates the Databricks Job from [jobs/airbnb_pipeline.json](jobs/airbnb_pipeline.json) |
| [notebooks/01_etl_city.py](notebooks/01_etl_city.py) | One city: raw → bronze → silver → gold metrics → features |
| [notebooks/06_train.py](notebooks/06_train.py), [07_score.py](notebooks/07_score.py) | Train on the training cities (MLflow + UC registry), score any city |
| [dashboards/](dashboards/) | AI/BI dashboard (`airbnb_spain.lvdash.json`) and its SQL datasets |
| [genie/](genie/) | Genie Agent instructions, example SQL, table comments |
| [reports/](reports/) | Week-1 model results and the city C report with run records |
| [docs/DEPLOY_UA.md](docs/DEPLOY_UA.md) | Step-by-step deployment guide for the team (Ukrainian) |
| [presentation/isd_airbnb_spain.pdf](presentation/isd_airbnb_spain.pdf) | Presentation (PDF; editable [.pptx](presentation/isd_airbnb_spain.pptx)) |
| [docs/assignment.pdf](docs/assignment.pdf) | The assignment brief |
| [tests/](tests/) | Unit tests (`uv run pytest`) |

## Run on Databricks

See [docs/DEPLOY_UA.md](docs/DEPLOY_UA.md). In short:

1. Put the raw files in `/Volumes/workspace/airbnb/raw/<city>/<snapshot>/listings.csv.gz`, or let the job download them.
2. Clone this repo as a Git folder, run `notebooks/00_setup_job`.
3. Run job `airbnb_pipeline` (parameters `cities`, `train`, `train_cities`).
4. Import `dashboards/airbnb_spain.lvdash.json`; create the Genie Agent from `genie/`.

A new city: add it to `config/cities.yml`, then run the job with `cities=["<city>"]`, `train=false`.

## Run locally

```bash
uv sync
uv run python scripts/fetch_data.py          # downloads Madrid and Sevilla into data/
uv run python scripts/run_local.py           # bronze → silver → gold → train → score (parquet in local_lake/)
uv run python scripts/check_sql.py           # runs every dashboard/Genie query against the local lake
uv run pytest
```

## Team

| member | contribution |
|---|---|
| _name_ | _to be filled by the team_ |
