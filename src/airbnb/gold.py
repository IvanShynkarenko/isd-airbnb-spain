"""Gold aggregates for the dashboard and Genie."""
from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def _share(room: str):
    return F.avg((F.col("room_type") == room).cast("double"))


def city_metrics(silver: DataFrame) -> DataFrame:
    return silver.groupBy("city", "snapshot_date").agg(
        F.count("*").alias("listings"),
        F.count("price").alias("listings_with_price"),
        F.median("price").alias("median_price"),
        F.median(F.when(F.col("room_type") == "Entire home/apt", F.col("price"))).alias("median_price_entire_home"),
        F.median(F.when(F.col("room_type") == "Private room", F.col("price"))).alias("median_price_private_room"),
        F.avg("availability_365").alias("avg_availability_365"),
        F.avg("review_scores_rating").alias("avg_review_score"),
        F.countDistinct("host_id").alias("hosts"),
        F.avg((F.col("calculated_host_listings_count") > 1).cast("double")).alias("share_multi_listing_hosts"),
        _share("Entire home/apt").alias("share_entire_home"),
        _share("Private room").alias("share_private_room"),
        _share("Shared room").alias("share_shared_room"),
        _share("Hotel room").alias("share_hotel_room"),
        F.avg(F.col("price_missing").cast("double")).alias("share_without_price"),
        F.avg((F.col("license_class") == "registered").cast("double")).alias("share_registered_license"),
    )


def neighbourhood_metrics(silver: DataFrame) -> DataFrame:
    return silver.groupBy("city", "neighbourhood_group", "neighbourhood").agg(
        F.count("*").alias("listings"),
        F.count("price").alias("listings_with_price"),
        F.median("price").alias("median_price"),
        F.avg("review_scores_rating").alias("avg_review_score"),
        _share("Entire home/apt").alias("share_entire_home"),
        F.avg("latitude").alias("latitude"),
        F.avg("longitude").alias("longitude"),
    )
