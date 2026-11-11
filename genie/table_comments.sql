-- Run once in the SQL Editor after the first successful job run. Genie (and Catalog Explorer) show these comments.
COMMENT ON TABLE workspace.airbnb_gold.city_metrics IS 'One row per city: listings, prices (EUR/night), hosts, availability, review scores, room-type shares. Source: Inside Airbnb listings snapshot.';
COMMENT ON TABLE workspace.airbnb_gold.neighbourhood_metrics IS 'One row per city and neighbourhood: listings, median price (EUR/night), average review score.';
COMMENT ON TABLE workspace.airbnb_gold.predictions IS 'One row per listing: actual price, model prediction, baseline prediction, error = predicted_price - price (negative = under-priced). split: train/test/no_price.';
COMMENT ON TABLE workspace.airbnb_gold.model_metrics IS 'Test-set accuracy per city (city=all = both training cities): MAE of model and baseline in EUR. population ok = price 10-1000 EUR, all_priced = any price.';
COMMENT ON TABLE workspace.airbnb_silver.listings IS 'Cleaned listings, one row per listing per snapshot. price in EUR/night, NULL when not advertised.';
ALTER TABLE workspace.airbnb_gold.city_metrics ALTER COLUMN median_price_entire_home COMMENT 'Median price (EUR/night) of room_type = Entire home/apt';
ALTER TABLE workspace.airbnb_gold.city_metrics ALTER COLUMN city COMMENT 'madrid = City A, sevilla = City B, barcelona = City C (lower case)';
ALTER TABLE workspace.airbnb_gold.predictions ALTER COLUMN error COMMENT 'predicted_price - price in EUR. Negative = model under-prices, positive = over-prices';
ALTER TABLE workspace.airbnb_gold.predictions ALTER COLUMN split COMMENT 'train / test / no_price. Use test for accuracy questions';
ALTER TABLE workspace.airbnb_gold.predictions ALTER COLUMN outlier_class COMMENT 'ok = price 10-1000 EUR; zero_or_tiny, extreme_high, no_price otherwise';
ALTER TABLE workspace.airbnb_gold.model_metrics ALTER COLUMN mae_model COMMENT 'Mean absolute error of the model on the test set, EUR';
ALTER TABLE workspace.airbnb_gold.model_metrics ALTER COLUMN mae_baseline COMMENT 'Mean absolute error of the baseline (median price for same room type and guests), EUR';
