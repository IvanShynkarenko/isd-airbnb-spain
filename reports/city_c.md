# The new client: Barcelona (city C)

**Why Barcelona.** It is Spain's other large Airbnb market, but it is regulated very differently from Madrid and Sevilla
(tourist licences have been frozen for years). We expected the market to *look* similar in the data and *behave*
differently, which makes it the hardest realistic test of the week-1 pipeline and model.

Snapshot: Inside Airbnb `spain/catalonia/barcelona/2026-09-17`, 15 236 listings. Barcelona was opened only after
the tag `week1-final` (commit `cc92d07`); the first run used that code and model unchanged.

## 1. First run (unchanged pipeline and model)

The only change before the run was the Barcelona entry in `config/cities.yml`. That is how the pipeline is designed
to take a new city, not a code change. Job `airbnb_pipeline`, parameters `cities=["barcelona"]`, `train=false`
(details: [city_c/first_run_databricks.md](city_c/first_run_databricks.md)).

| question | answer |
|---|---|
| Did it run? | **Yes**, in 1 min 52 s, no task failed. |
| What failed? | Nothing crashed. The download from Inside Airbnb worked from Databricks, the schema matched (same 90 columns), prices and bathrooms parsed, no listing lost its id. Row count 15 236 = Python `csv` count. |
| What came out? | Bronze, silver, gold metrics, features and predictions for all 15 236 listings, and test-set metrics. |
| What went wrong silently? | **Every** Barcelona neighbourhood (68 of 68) was unknown to the model. The pipeline scored the city anyway, with no warning. |
| MAE on Barcelona (test, price 10–1000 EUR) | **80.65 EUR**, vs 49.64 EUR on Madrid + Sevilla. The baseline was 85.02 EUR. |

The model ran and beat the baseline, but only by 5%, against 25% in the training cities.

## 2. Why the model did not transfer

| | Madrid | Sevilla | Barcelona |
|---|---:|---:|---:|
| median price, listings 10–1000 EUR | 150 | 157 | **188** |
| median price, stays under 30 nights | 157 | 154 | **246** |
| share of listings with minimum stay ≥ 30 nights | 12.5% | 1.8% | **33.5%** |
| neighbourhoods the model has seen | all | all | **none** |
| price spread (IQR / median) | 0.84 | 0.63 | **0.98** |
| share of priced listings above 1000 EUR | 0.9% | 0.9% | **2.4%** |

1. **A price level the model never saw.** Short-stay Barcelona listings cost 246 EUR at the median, 57% more than in
   Madrid or Sevilla. The model predicts Madrid/Sevilla prices for them. On the test set its mean error is
   **−69 EUR** (it under-prices), and −98 EUR on short stays. The error grows with the price: −1 EUR below 100 EUR,
   −80 EUR at 200–300 EUR, −171 EUR at 300–500 EUR.
2. **A feature that means something different.** `minimum_nights` is the model's second most important feature. In
   Madrid a 30+ night minimum marks a niche of cheaper mid-term rentals. In Barcelona, because of the licence freeze,
   a third of all listings are mid-term. The model prices that segment well (MAE 27 EUR) and the short-stay segment
   badly (MAE 108 EUR).
3. **A feature that means nothing.** `neighbourhood` is the third most important feature. In a new city every
   neighbourhood is unknown, and the one-hot encoder maps all of them to the same "unknown" vector. Training the same
   model without `neighbourhood` gives 67.4 EUR on Barcelona (−12 EUR) and 51.4 EUR on Madrid + Sevilla (+1.7 EUR).
   So, for a city with no training data, the feature does more harm than good.
4. **A harder city anyway.** Even a baseline built from Barcelona's own training prices only reaches 81.2 EUR, against
   66 EUR for the Madrid + Sevilla baseline at home. Barcelona prices are more spread out, so part of the gap would
   stay even with a perfect transfer.

## 3. What we changed

| # | change | kind | why | commit |
|---|---|---|---|---|
| 0 | Barcelona entry in `config/cities.yml` | onboarding (configuration) | the designed way to add a city | `a6d3ef3` |
| 1 | Scoring records `unseen_<column>_share` per city in `model_metrics` and warns when it is above 20% | **pipeline fix** | the first run scored a city with 100% unknown neighbourhoods silently; the pipeline should have shown this from the start | `2c136b7` |
| 2 | Retrain on the training split of Madrid + Sevilla + **Barcelona** (`train_cities` job parameter; no code change) | **model change** | the model never saw Barcelona's price level or neighbourhoods; Barcelona's 80% training split fixes both | job run 996010984346098, model **v2** |

Considered and not adopted:
- **Drop `neighbourhood` for all cities.** This helps a city with no data (67.4 EUR), but once Barcelona's training
  data is used the feature helps again. Change 2 makes it unnecessary for Barcelona. It is the right fallback for a
  *future* new city before its data is in, and change 1 now flags that situation.
- **Raise `MAX_PRICE` for Barcelona.** 2.4% of Barcelona priced listings are above 1000 EUR (0.9% elsewhere). We kept
  one threshold for all cities, so that the populations stay comparable, and report the `all_priced` MAE next to it.

The Barcelona test split (20%, the same hash rule) was never used for training or for choosing between options.
Options were compared on it once each, and all are reported here.

## 4. The numbers side by side (test split, listings priced 10–1000 EUR, EUR)

| | MAE |
|---|---:|
| Baseline on Barcelona: Madrid + Sevilla medians (the week-1 baseline) | 85.02 |
| Baseline on Barcelona: Barcelona's own training medians | 81.16 |
| Model on Madrid + Sevilla (week 1, v1) | **49.64** |
| Model on Barcelona, first run (v1, unchanged) | **80.65** |
| Model on Barcelona after change 2 (v2) | **47.85** |
| Model on Madrid + Sevilla after change 2 (v2) | 50.05 (Madrid 50.15, Sevilla 49.80) |

Including listings above 1000 EUR (`all_priced`): first run 122.99 vs baseline 125.48; after change 2: 81.83.
After change 2 the job's baseline is built from all three cities' training medians (82.74 on Barcelona); the two
baselines in the table are the fixed references.

## 5. Explaining the gap

The first-run gap (80.65 vs 49.64 EUR) comes from transfer, not from a broken pipeline. The model learned Madrid and
Sevilla prices and applied them to a market that is about 57% more expensive for short stays, with a different mix of
stay lengths and with neighbourhoods it had never seen. It under-priced almost every expensive listing.

With Barcelona's training data (change 2), the Barcelona error drops from 80.65 to 47.85 EUR, the level of the other
cities, and 41% below Barcelona's own-data baseline. The training cities lose 0.3–0.8 EUR. The remaining gap is about the price spread: Barcelona's own baseline is 81 EUR, against
66 EUR at home, so its MAE stays a little higher in absolute terms.

**What this says about the pipeline.** As a pipeline it is a product: one config line and one job run took Barcelona
from raw file to predictions, without a failure. As a *model* it is city-specific. A new client needs its own
training data, or at least a check like change 1 that says when it does not have it.
