# Week 1 — model results (Madrid + Sevilla)

Test set: 20% of listings per city, deterministic by `xxhash64(id)`, held out before any model choice.
The model was chosen by 5-fold CV on the training rows only (HGB 50.5 EUR vs Ridge 57.7 EUR CV MAE).
Model: `HistGradientBoostingRegressor` (absolute-error loss) on `log1p(price)`, 21 numeric + 4 one-hot categorical features.
Baseline (from the brief): median training price for the same `room_type` and `accommodates`.

Numbers below come from a local run (`scripts/run_local.py --stage all`). The Databricks run should match closely;
update this file from `workspace.airbnb_gold.model_metrics` after the smoke test.

## MAE on the test set, EUR

Population `ok` = price between 10 and 1000 EUR (what the model is trained for, 99% of priced listings).
Population `all_priced` = every test listing with a price, including the outliers.

| city | population | n | model MAE | baseline MAE | improvement | model median AE | model MAPE |
|---|---|---:|---:|---:|---:|---:|---:|
| Madrid | ok | 3 763 | **49.94** | 67.09 | −25.6% | 25.56 | 26% |
| Sevilla | ok | 1 510 | **49.12** | 63.38 | −22.5% | 29.29 | 25% |
| both | ok | 5 273 | **49.71** | 66.02 | −24.7% | 26.66 | 26% |
| Madrid | all_priced | 3 794 | 65.87 | 83.41 | −21.0% | 25.78 | 27% |
| Sevilla | all_priced | 1 526 | 74.79 | 89.22 | −16.2% | 29.57 | 26% |
| both | all_priced | 5 320 | 68.43 | 85.08 | −19.6% | 27.06 | 26% |

The 47 outlier listings in the test set (0.9%) add about 19 EUR to the combined MAE (68.4 vs 49.7): a few
listings priced at thousands of EUR dominate an average. The typical error (median) is about 27 EUR either way.

## What drives the predictions (permutation importance, MAE increase in EUR when shuffled)

| feature | EUR |
|---|---:|
| accommodates | 11.4 |
| minimum_nights | 9.9 |
| neighbourhood | 5.0 |
| bedrooms | 4.3 |
| bathrooms | 3.2 |
| calculated_host_listings_count | 2.6 |
| room_type | 2.6 |
| dist_center_km | 2.4 |
| number_of_reviews | 1.9 |
| property_type | 1.5 |

## Where it errs

Errors are largest for entire homes (MAE 57 EUR in Madrid, 52 EUR in Sevilla). The mean error is negative: the model
under-prices on average, because absolute-error loss targets the median and prices are right-skewed.
