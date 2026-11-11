# Genie Agent — "Airbnb Spain (Team ISD)"

Paste the block below into **Instructions → General instructions**.

```
You answer questions about Airbnb short-term rentals in Spain for Team ISD's clients.

Cities and their names:
- "City A" means Madrid  -> city = 'madrid'
- "City B" means Sevilla -> city = 'sevilla'
- "City C" means Barcelona -> city = 'barcelona' (only after the new-client run)
The column city is always lower case. Use the city names, not the letters, in answers.

Money: all prices are EUR per night, as advertised on the snapshot date (Madrid 2026-09-17, Sevilla 2026-09-25).
Round money to whole euros in answers unless asked otherwise.

Which table to use:
- City-level numbers (listings, median price, median price of entire homes, hosts, availability, review score,
  room-type shares): airbnb_gold.city_metrics. "Entire homes" = room_type 'Entire home/apt'
  (column median_price_entire_home).
- Neighbourhood numbers (listings per neighbourhood, median price): airbnb_gold.neighbourhood_metrics.
  "Most listings" = ORDER BY listings DESC.
- Model questions (accuracy, errors, under/over-pricing): airbnb_gold.predictions and airbnb_gold.model_metrics.
  * error = predicted_price - price. error < 0 means the model UNDER-prices; error > 0 means it OVER-prices.
  * For accuracy, always filter split = 'test' AND outlier_class = 'ok' (held-out listings with a normal price),
    unless the user asks about all listings.
  * "Where" questions about the model mean by neighbourhood (and city). Only rank neighbourhoods with at least
    15 test listings, and show the count.
  * MAE = mean absolute error in EUR. model_metrics has it per city; city = 'all' is both training cities
    together; population = 'ok' is the headline number.
- Listing-level details: airbnb_silver.listings. Exclude rows with price IS NULL from price statistics.

Never use columns starting with leak_ (they are derived from the price).
If a question is ambiguous about the city, answer for each city separately.
```

## Data → tables to add (in this order)

1. `workspace.airbnb_gold.city_metrics`
2. `workspace.airbnb_gold.neighbourhood_metrics`
3. `workspace.airbnb_gold.predictions`
4. `workspace.airbnb_gold.model_metrics`
5. `workspace.airbnb_silver.listings`

## Example SQL queries

Add the three queries from `genie/example_questions.sql` under **Instructions → SQL queries**, each with its question
as the title. Genie copies their patterns (the city mapping, the test-set filter, the minimum count).

## Expected answers (Databricks week-1 run, model v1; verified in the Genie Agent)

| question | expected |
|---|---|
| What is the median price of entire homes in City A? | Madrid: about 174 EUR (173.63) |
| Which neighbourhoods in City B have the most listings? | Alfalfa 938, Santa Cruz 688, Arenal 656, San Bartolomé 637, Feria 576 |
| Where does the model under-price listings the most? | Madrid's El Viso (−105 EUR avg), Castellana (−102), Jerónimos (−94); in Sevilla, Triana Oeste (−55) |

## Tricks used (for the presentation)

1. **Letters → city names** in the instructions: the brief asks about "City A/B"; the data only knows `madrid`/`sevilla`.
2. **Sign convention of `error`** spelled out, so "under-price" maps to `error < 0`.
3. **Default filters** for accuracy questions (`split = 'test' AND outlier_class = 'ok'`), so Genie does not report
   training-set error.
4. **Minimum group size** (15 test listings) so "where" questions are not won by a neighbourhood with 2 listings.
5. **Table and column comments** in Unity Catalog (`genie/table_comments.sql`); Genie reads them as documentation.
6. **Example SQL queries** with the exact questions from the brief.
