# Week 1 — model results (Madrid + Sevilla)

Test set: 20% of listings per city, deterministic by `xxhash64(id)` (Madrid 20.2%, Sevilla 19.6%), held out before
any model choice. The model was chosen by 5-fold CV on the training rows only (HGB 50.5 EUR vs Ridge 57.7 EUR CV MAE).
Model: `HistGradientBoostingRegressor` (absolute-error loss) on `log1p(price)`, 21 numeric + 4 one-hot categorical
features. Baseline (from the brief): median training price for the same `room_type` and `accommodates`.

Source: `workspace.airbnb_gold.model_metrics` on Databricks, job `airbnb_pipeline`, model `price_model` **v1**.

## MAE on the test set, EUR

Population `ok` = price between 10 and 1000 EUR (what the model is trained for, 99% of priced listings).
Population `all_priced` = every test listing with a price, including the outliers.

| city | population | n | model MAE | baseline MAE | improvement |
|---|---|---:|---:|---:|---:|
| Madrid | ok | 3 763 | **49.89** | 67.09 | −25.6% |
| Sevilla | ok | 1 510 | **49.01** | 63.38 | −22.7% |
| both | ok | 5 273 | **49.64** | 66.02 | −24.8% |
| Madrid | all_priced | 3 794 | 65.82 | 83.41 | −21.1% |
| Sevilla | all_priced | 1 526 | 74.66 | 89.22 | −16.3% |
| both | all_priced | 5 320 | 68.36 | 85.08 | −19.7% |

The 47 outlier listings in the test set (0.9%) add about 19 EUR to the combined MAE (68.4 vs 49.6): a few
listings priced at thousands of EUR dominate an average. The typical error (median absolute error) is about 27 EUR.

The local run (`scripts/run_local.py`, scikit-learn 1.9) gives the same baseline to the cent and a model MAE within
0.3 EUR (49.71 combined); the difference comes from the scikit-learn version on serverless.

## What drives the predictions (permutation importance on the test set, MAE increase in EUR when shuffled; local run)

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
under-prices on average, because absolute-error loss targets the median and prices are right-skewed. It under-prices
expensive listings most (−106 EUR on average at 300–500 EUR) and premium Madrid neighbourhoods (El Viso, Castellana,
Jerónimos: about −100 EUR on average).
