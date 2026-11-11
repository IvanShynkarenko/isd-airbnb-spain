-- name: city_metrics
SELECT city, listings, listings_with_price, median_price, median_price_entire_home, median_price_private_room,
       avg_availability_365, avg_review_score, hosts, share_multi_listing_hosts, share_without_price,
       share_registered_license
FROM workspace.airbnb_gold.city_metrics;

-- name: room_mix
SELECT city, room_type, share
FROM workspace.airbnb_gold.city_metrics
LATERAL VIEW stack(4, 'Entire home/apt', share_entire_home, 'Private room', share_private_room,
                      'Shared room', share_shared_room, 'Hotel room', share_hotel_room) s AS room_type, share;

-- name: neighbourhoods
SELECT city, neighbourhood, neighbourhood_group, listings, listings_with_price, median_price, avg_review_score
FROM workspace.airbnb_gold.neighbourhood_metrics
WHERE listings_with_price >= 20;

-- name: top_neighbourhoods
SELECT city, neighbourhood, median_price, listings
FROM (
  SELECT city, neighbourhood, median_price, listings,
         ROW_NUMBER() OVER (PARTITION BY city ORDER BY median_price DESC) AS rn
  FROM workspace.airbnb_gold.neighbourhood_metrics
  WHERE listings_with_price >= 20
) WHERE rn <= 10;

-- name: underpriced_neighbourhoods
SELECT city, neighbourhood, COUNT(*) AS test_listings, AVG(error) AS avg_error
FROM workspace.airbnb_gold.predictions
WHERE split = 'test' AND outlier_class = 'ok'
GROUP BY city, neighbourhood
HAVING COUNT(*) >= 15
ORDER BY avg_error ASC
LIMIT 12;

-- name: listings_ok
SELECT city, room_type, accommodates, price,
       CASE WHEN minimum_nights >= 30 THEN '30+ nights (mid-term)' ELSE 'under 30 nights' END AS stay_type,
       availability_365, review_scores_rating
FROM workspace.airbnb_silver.listings
WHERE outlier_class = 'ok';

-- name: model_vs_baseline
SELECT city, predictor, mae
FROM workspace.airbnb_gold.model_metrics
LATERAL VIEW stack(2, 'model', mae_model, 'baseline (room type x guests)', mae_baseline) s AS predictor, mae
WHERE population = 'ok';

-- name: test_predictions
SELECT city, id, neighbourhood, room_type, accommodates, price, predicted_price, baseline_price, error, abs_error
FROM workspace.airbnb_gold.predictions
WHERE split = 'test' AND outlier_class = 'ok';

-- name: worst_predictions
SELECT city, id, neighbourhood, room_type, accommodates,
       ROUND(price, 0) AS price, ROUND(predicted_price, 0) AS predicted, ROUND(error, 0) AS error,
       CASE WHEN error < 0 THEN 'under-priced' ELSE 'over-priced' END AS direction
FROM workspace.airbnb_gold.predictions
WHERE split = 'test' AND outlier_class = 'ok'
ORDER BY abs_error DESC
LIMIT 30;

-- name: city_c_runs
-- model_metrics keeps only the latest model per city, so the first-run numbers come from reports/city_c.md
SELECT * FROM VALUES
  ('1. first run (v1, unchanged)', 'baseline (Madrid + Sevilla medians)', 85.02),
  ('1. first run (v1, unchanged)', 'model', 80.65),
  ('2. after retrain with Barcelona (v2)', 'baseline (Barcelona own medians)', 81.16),
  ('2. after retrain with Barcelona (v2)', 'model', 47.85)
  AS t(stage, predictor, mae);
