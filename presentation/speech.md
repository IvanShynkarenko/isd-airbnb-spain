# Speech, slide by slide

About 12–13 minutes plus the live demo. Each slide gives a suggested time. Split the slides between team members by
topic: intro and EDA · architecture and pipeline · model · city C · demo and closing.

---

## 1. Can a Madrid + Sevilla price model serve Barcelona? (0:30)

Good afternoon. We are Team ISD, and our region is Spain.

Our start-up had two clients, in Madrid and Sevilla. For them we built a lakehouse over Airbnb data, a dashboard, a
Genie agent and a model that suggests a nightly price. Then sales signed a third client, in Barcelona, and asked
whether we could have prices there by Friday.

This talk answers one question: is what we built a product, or a prototype that only works on the data it was built on?

## 2. The task: price suggestions for two clients, then a third (0:45)

The three cities come from Inside Airbnb, the latest snapshot of each:
- Madrid: about 23 000 listings, snapshot from September 17.
- Sevilla: about 8 400, from September 25.
- Barcelona: about 15 000, from September 17.

All prices are in euros per night.

In week one we worked only with Madrid and Sevilla. That covered the analysis, the lakehouse, one job that takes the
city as a parameter, the model, the dashboard and Genie.

Barcelona stayed unseen until we froze that work with a git tag. In week two we ran the frozen pipeline on Barcelona,
fixed what broke, and measured the gap.

## 3. Analysis: missing prices mark inactive listings, and two columns are the price in disguise (1:15)

Three findings from the analysis shaped everything after it.

**First, prices are not missing at random.** 19% of Madrid listings have no price, and 8% of Sevilla's. When we looked
at which listings, almost all of them were inactive: no availability in the next year and no reviews in the last
twelve months. In Madrid, 99% of those inactive listings have no price. So our model is a model of active listings,
and we say so.

**Second, outliers.** Less than one percent of listings cost more than 1000 euros a night, up to 36 000. Most of them
were never booked; they look like parked or mistyped prices. We flag them instead of deleting them. We train without
them, and we report the error both with and without them.

**Third, the leakage review.** The 2026 files contain new columns:
- `price_quote_price_per_night` equals the price in 100% of rows.
- `estimated_revenue_l365d` is exactly price times occupancy; the ratio is 1.000.

We found them by checking ratios, not correlations; the correlation was only 0.48. Both are excluded, together with
occupancy and availability, which are consequences of the price.

## 4. Architecture: one parameterised job turns a raw file into predictions (1:00)

This is our medallion lakehouse on Databricks Free Edition.

1. **Volume.** The raw file lands in a Unity Catalog volume, one folder per city and snapshot.
2. **Bronze.** The CSV as text, plus lineage columns, so nothing can fail on types.
3. **Silver.** Typed and cleaned. Prices are parsed from strings like "$1,234.00", bathrooms from text. Problems are
   flagged, and no rows are dropped.
4. **Gold.** City and neighbourhood metrics for the dashboard, model features, predictions and metrics.

All of it runs as one job. For each city it does the ETL. Then, if asked, it trains on the training cities. Then, for
each city, it scores.

The city is only a parameter, and everything city-specific lives in one config file. Each write replaces only its own
city's rows, so cities can be re-run independently. It all runs on serverless and costs nothing.

## 5. The model beats the baseline by a quarter in both training cities (1:15)

The baseline is the one from the brief: the median price for the same room type and number of guests, computed on
training data.

Our model is gradient boosting on the log of the price. We chose it over a ridge regression by cross-validation on the
training rows only. The test set is 20% of listings per city, picked by a hash of the listing id and set aside before
any choice.

On that test set:
- the baseline is wrong by 66 euros on average, and the model by 50;
- that is 26% better in Madrid and 23% better in Sevilla.

On the right is what drives the predictions:
- **number of guests** first;
- **minimum nights** second, because 30-plus-night rentals are much cheaper per night;
- **neighbourhood** third.

Remember the last two; they matter in a minute.

## 6. The new client: Barcelona (0:15)

So, sales asks: "Your pipeline takes the city as a parameter, right?"

We added Barcelona to the config, changed nothing else, and ran the job.

## 7. First run: nothing crashed, and the model barely beat the baseline (1:00)

The good news first: the pipeline ran. The job finished in under two minutes and downloaded the file itself. All
15 236 listings went through bronze, silver and features, exactly the count in the source file. There was no schema
problem and no parsing problem.

The bad news is the number. The model's error in Barcelona was 81 euros, against 50 at home, and the baseline was 85.
So the model was only 5% better than a median, instead of 25%.

There was also a quiet problem. All 68 Barcelona neighbourhoods were unknown to the model, and the pipeline scored the
city anyway, without a single warning.

## 8. Why it did not transfer: a price level, a stay mix and neighbourhoods it never saw (1:30)

We found three reasons.

**A price level the model never saw.** Short stays in Barcelona cost 246 euros at the median, against about 155 in
Madrid and Sevilla. The model predicts Madrid prices. The chart on the right shows the result: below 100 euros the
error is almost zero, and the more expensive the listing, the more the model under-prices it, down to minus 394 euros.

**A feature that means something different.** Remember minimum nights. In Madrid, a 30-night minimum marks a small
niche. Barcelona has frozen tourist licences, so a third of all its listings are mid-term rentals. The model handles
that third well, with an error of 27 euros. It handles the short stays badly, with an error of 108.

**A feature that means nothing.** Remember neighbourhood. In a new city every neighbourhood is unknown. We tested it:
the same model trained without neighbourhood does 12 euros better on Barcelona.

And Barcelona is simply harder. Even a baseline built from Barcelona's own prices is wrong by 81 euros, because prices
there are more spread out.

## 9. What we changed: one pipeline fix and one model change (1:00)

We sorted every change into the two kinds the brief asks for.

**The pipeline fix.** The pipeline should have told us it was scoring a city where every neighbourhood was unknown. Now
scoring records, for each categorical feature, the share of values the model never saw. It writes that share to the
metrics table and prints a warning above 20%.

**The model change.** The model had never seen Barcelona's prices, so we retrained it on the training split of all
three cities. That was a job parameter, not new code. The result is model version 2.

**Considered and not adopted:**
- Dropping neighbourhood for every city. It helps with no data, but with Barcelona's data the feature helps again.
- A separate price cap for Barcelona. One cap keeps the cities comparable.

The Barcelona test split was never used for training or for choosing.

## 10. Barcelona's own data cuts the error from 81 to 48 euros (1:00)

These are the numbers the brief asks for, side by side:

| | MAE |
|---|---:|
| Baseline on Barcelona | 85 euros |
| Our model at home | 50 |
| Our model on Barcelona, first run | 81 |
| After retraining with Barcelona data | 48 |

That is back to the level of the training cities. Madrid and Sevilla got slightly worse, by less than a euro.

So the gap was transfer, not a broken pipeline. With outliers included, the numbers are larger, but the story is the
same.

## 11. Dashboard and Genie (2–3 minutes, live demo)

Let me show it live.

**Dashboard.** Every page title states a finding, not a topic.
1. Open **City overview**: Madrid has almost three times more listings, but the typical night costs about the same.
2. Open **Madrid vs Sevilla**: the same price level, but a different market. Madrid has more private rooms and
   mid-term rentals; Sevilla is mostly entire homes.
3. Open **Model**: error against the baseline per city, predicted against actual, where the model under-prices, and at
   the bottom Barcelona before and after.

**Genie.** Ask the three questions from the brief:
- "What is the median price of entire homes in City A?" Answer: 174 euros.
- "Which neighbourhoods in City B have the most listings?" Answer: Alfalfa, Santa Cruz, Arenal.
- "Where does the model under-price listings the most?" Answer: El Viso, Castellana and Jerónimos in Madrid.

What made Genie answer correctly:
- The instructions map "City A" and "City B" to the real city names.
- They spell out that a negative error means under-pricing.
- They make accuracy questions use only the test set, by default.
- "Where" questions only rank neighbourhoods with enough listings.
- Every key column has a comment in Unity Catalog.
- The three questions are stored as example SQL.

## 12. Challenges, and who did what (1:00)

Three things were harder than expected.

**Free Edition.** You cannot create bundles from the UI, and internet access is restricted. So a notebook creates the
job, and the raw files have a fallback through the volume.

**A bug we caught before Databricks did.** Airbnb listing ids have 19 digits. Our fallback type conversion for older
Spark clients turned more than half of them into nulls. That would have silently broken the train/test split. A code
review caught it, and now the pipeline fails loudly if any id is missing.

**The leaks.** They were found only because we checked ratios, not correlations.

*(Each member says in one sentence what they did.)*

## 13. The pipeline is a product. The model is per city (0:30)

To answer the question from the start:

**The pipeline is a product.** One config line took Barcelona from a raw file to predictions without a single failure.

**The model is per city.** A new client needs its own training data. Now the pipeline tells us when it doesn't have it.

Next, we would:
- keep the metrics history for every model version;
- add a fallback model without neighbourhood for a city that has no prices yet.

Thank you. We are happy to take questions.

---

## Likely questions

- **Why not train a separate model per city?**
  - A Barcelona-only model does a little better on Barcelona (45 vs 48).
  - But one model for all cities is simpler to run and keeps Madrid and Sevilla at the same level.
  - Per-city models are a reasonable next step once a city has enough data.
- **Isn't using Barcelona's training data cheating?**
  - No. The brief allows model changes. We only used Barcelona's 80% training split.
  - The 20% test split was used only for evaluation, and every option we tried is reported.
- **Why MAE and not RMSE?**
  - The brief asks for MAE, in euros. It is easy to explain to a client: "on average we are this many euros off."
  - We also report the median error and MAPE.
- **Why log price with absolute-error loss?**
  - Prices are heavily right-skewed. On a log scale with absolute-error loss the model targets the median price, which
    is what MAE rewards.
  - The side effect is a slight under-pricing on average, and we show it.
- **Why didn't the download fail, when Free Edition restricts the internet?**
  - It worked for this site in our workspace.
  - If it hadn't, the job would stop with a message naming the URL and the exact volume path to upload the file to.
