"""Silver: typed, cleaned listings - one row per listing per snapshot, nothing dropped.

Rows are never filtered here; problems are flagged (price_missing, outlier_class) so the
dashboard can still count them and the model step decides what to train on.
"""
from __future__ import annotations

from pyspark.sql import Column, DataFrame
from pyspark.sql import functions as F

# Price bounds in EUR/night (see notebooks/eda_madrid_sevilla.ipynb, section "Outliers"):
# below 10 EUR is a placeholder, not a nightly price; above 1000 EUR are mostly listings with no
# reviews and near-full availability (parked or mistyped prices, up to 36 883 EUR). Together < 1%.
MIN_PRICE = 10.0
MAX_PRICE = 1000.0

REVIEW_SCORES = ["rating", "accuracy", "cleanliness", "checkin", "communication", "location", "value"]

# Columns derived from the price (or from bookings driven by it). Kept with a leak_ prefix only so
# the EDA leakage review can show the relationship; never used as model features.
LEAK_SOURCE_COLUMNS = ["price_quote_price_per_night", "estimated_revenue_l365d", "estimated_occupancy_l365d"]


def _blank_to_null(c: Column) -> Column:
    return F.when(F.trim(c) == "", None).otherwise(c)


def parse_price(c: Column) -> Column:
    """'$1,234.00' -> 1234.0; '' or null -> null."""
    return F.regexp_replace(_blank_to_null(c), r"[$,\s]", "").try_cast("double")


def parse_bathrooms(c: Column) -> tuple[Column, Column]:
    """bathrooms_text -> (number of baths, is shared). 'Half-bath' -> 0.5."""
    t = F.lower(_blank_to_null(c))
    num = F.regexp_extract(t, r"^(\d+(\.\d+)?)", 1)
    baths = (
        F.when(t.isNull(), None)
        .when(num != "", num.try_cast("double"))
        .when(t.contains("half-bath"), F.lit(0.5))
    )
    shared = F.when(t.isNull(), None).otherwise(t.contains("shared"))
    return baths, shared


def license_class(c: Column) -> Column:
    """registered / exempt / pending / none (the raw text is free-form)."""
    t = F.lower(F.trim(c))
    return (
        F.when(t.isNull() | (t == ""), "none")
        .when(t.startswith("exempt"), "exempt")
        .when(t.startswith("en proceso") | t.startswith("pending"), "pending")
        .otherwise("registered")
    )


def _bool(c: str) -> Column:
    return F.when(F.col(c) == "t", True).when(F.col(c) == "f", False)


def _num(c: str, t: str) -> Column:
    return _blank_to_null(F.col(c)).try_cast(t)


def to_silver(bronze: DataFrame) -> DataFrame:
    baths, shared = parse_bathrooms(F.col("bathrooms_text"))
    price = parse_price(F.col("price"))
    lic = _blank_to_null(F.col("license"))
    df = bronze.select(
        _num("id", "bigint").alias("id"),
        "city",
        "snapshot_date",
        _num("host_id", "bigint").alias("host_id"),
        _num("hosts_time_as_host_years", "int").alias("host_years"),  # host_since is empty in 2026 files
        _bool("host_is_superhost").alias("host_is_superhost"),
        _bool("host_identity_verified").alias("host_identity_verified"),
        _num("host_listings_count", "int").alias("host_listings_count"),
        F.col("neighbourhood_cleansed").alias("neighbourhood"),
        F.col("neighbourhood_group_cleansed").alias("neighbourhood_group"),
        _num("latitude", "double").alias("latitude"),
        _num("longitude", "double").alias("longitude"),
        "property_type",
        "room_type",
        _num("accommodates", "int").alias("accommodates"),
        baths.alias("bathrooms"),
        shared.alias("bathrooms_shared"),
        _num("bedrooms", "int").alias("bedrooms"),
        _num("beds", "int").alias("beds"),
        F.size(F.from_json(_blank_to_null(F.col("amenities")), "array<string>")).alias("amenities_count"),
        F.col("amenities").alias("amenities_raw"),
        price.alias("price"),
        _num("minimum_nights", "int").alias("minimum_nights"),
        _num("maximum_nights", "int").alias("maximum_nights"),
        _num("availability_30", "int").alias("availability_30"),
        _num("availability_60", "int").alias("availability_60"),
        _num("availability_90", "int").alias("availability_90"),
        _num("availability_365", "int").alias("availability_365"),
        _bool("has_availability").alias("has_availability"),
        _num("number_of_reviews", "int").alias("number_of_reviews"),
        _num("number_of_reviews_ltm", "int").alias("number_of_reviews_ltm"),
        _num("first_review", "date").alias("first_review"),
        _num("last_review", "date").alias("last_review"),
        *[_num(f"review_scores_{s}", "double").alias(f"review_scores_{s}") for s in REVIEW_SCORES],
        _num("reviews_per_month", "double").alias("reviews_per_month"),
        lic.isNotNull().alias("has_license"),
        license_class(F.col("license")).alias("license_class"),
        _num("calculated_host_listings_count", "int").alias("calculated_host_listings_count"),
        *[_num(c, "double").alias(f"leak_{c}") for c in LEAK_SOURCE_COLUMNS],
    )
    # from_json of a null string gives size -1; keep it null
    df = df.withColumn("amenities_count", F.when(F.col("amenities_count") >= 0, F.col("amenities_count")))
    return df.withColumn("price_missing", F.col("price").isNull()).withColumn(
        "outlier_class",
        F.when(F.col("price").isNull(), "no_price")
        .when(F.col("price") < MIN_PRICE, "zero_or_tiny")
        .when(F.col("price") > MAX_PRICE, "extreme_high")
        .otherwise("ok"),
    )
