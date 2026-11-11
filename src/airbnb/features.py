"""Model features (gold). See notebooks/eda_madrid_sevilla.ipynb section 6 for the leakage review."""
from __future__ import annotations

# Raw columns that must never reach the model: computed from the price, or an outcome of it.
LEAKAGE_COLUMNS = [
    "price_quote_checkin_date",
    "price_quote_checkout_date",
    "price_quote_total_price",
    "price_quote_price_per_night",
    "price_quote_raw",
    "estimated_revenue_l365d",
    "estimated_occupancy_l365d",
    "availability_30",
    "availability_60",
    "availability_90",
    "availability_365",
    "availability_eoy",
    "has_availability",
]

from pyspark.sql import Column, DataFrame
from pyspark.sql import functions as F

from airbnb.config import CityConfig

TEST_PCT = 20  # % of listings per city held out as the test set

# Amenities with a clear price signal in the EDA (section 7); matched as lower-case substrings.
AMENITY_FLAGS = {
    "has_air_conditioning": "air conditioning",
    "has_dishwasher": "dishwasher",
    "has_elevator": "elevator",
    "has_pool": "pool",
    "has_free_street_parking": "free street parking",
    "has_lock_on_bedroom_door": "lock on bedroom door",
    "has_patio_or_balcony": "patio or balcony",
}

NUMERIC = [
    "accommodates",
    "bedrooms",
    "beds",
    "bathrooms",
    "bathrooms_shared",
    "amenities_count",
    *AMENITY_FLAGS,
    "dist_center_km",
    "minimum_nights",
    "host_years",
    "host_is_superhost",
    "calculated_host_listings_count",
    "number_of_reviews",
    "review_scores_rating",
    "review_scores_location",
]
CATEGORICAL = ["room_type", "property_type", "neighbourhood", "license_class"]
FEATURE_COLUMNS = NUMERIC  # numeric model inputs; CATEGORICAL are one-hot encoded in the model


def assign_split(df: DataFrame, test_pct: int = TEST_PCT) -> DataFrame:
    """Deterministic per-listing split: the same id always lands in the same split."""
    return df.withColumn("split", F.when(F.pmod(F.xxhash64("id"), F.lit(100)) < test_pct, "test").otherwise("train"))


def haversine_km(lat: str, lon: str, lat0: float, lon0: float) -> Column:
    la1, lo1 = F.radians(F.col(lat)), F.radians(F.col(lon))
    la0, lo0 = F.radians(F.lit(lat0)), F.radians(F.lit(lon0))
    a = F.sin((la1 - la0) / 2) ** 2 + F.cos(la0) * F.cos(la1) * F.sin((lo1 - lo0) / 2) ** 2
    return F.lit(2 * 6371.0) * F.asin(F.sqrt(a))


def build_features(silver: DataFrame, c: CityConfig) -> DataFrame:
    """One row per listing of city c (every listing, so the model can score all of them)."""
    am = F.lower(F.coalesce(F.col("amenities_raw"), F.lit("")))
    df = silver.filter(F.col("city") == c.name).select(
        "id",
        "city",
        "snapshot_date",
        "neighbourhood_group",
        "latitude",
        "longitude",
        "price",
        "outlier_class",
        *CATEGORICAL,
        *[F.col(n).cast("double").alias(n) for n in NUMERIC if n not in AMENITY_FLAGS and n != "dist_center_km"],
        *[am.contains(s).cast("double").alias(n) for n, s in AMENITY_FLAGS.items()],
        haversine_km("latitude", "longitude", c.center_lat, c.center_lon).alias("dist_center_km"),
    )
    df = df.withColumn("is_trainable", F.col("outlier_class") == "ok")
    return assign_split(df)
