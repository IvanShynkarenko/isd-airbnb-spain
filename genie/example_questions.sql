-- question: What is the median price of entire homes in City A?
SELECT city, ROUND(median_price_entire_home, 2) AS median_price_entire_home_eur
FROM workspace.airbnb_gold.city_metrics
WHERE city = 'madrid';

-- question: Which neighbourhoods in City B have the most listings?
SELECT neighbourhood, listings
FROM workspace.airbnb_gold.neighbourhood_metrics
WHERE city = 'sevilla'
ORDER BY listings DESC
LIMIT 10;

-- question: Where does the model under-price listings the most?
SELECT city, neighbourhood, COUNT(*) AS test_listings, ROUND(AVG(error), 1) AS avg_error_eur,
       ROUND(AVG(CASE WHEN error < 0 THEN 1 ELSE 0 END), 2) AS share_under_priced
FROM workspace.airbnb_gold.predictions
WHERE split = 'test' AND outlier_class = 'ok'
GROUP BY city, neighbourhood
HAVING COUNT(*) >= 15
ORDER BY avg_error_eur ASC
LIMIT 10;
