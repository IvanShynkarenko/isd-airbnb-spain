"""Per-city ETL orchestration shared by Databricks notebooks and the local runner."""
from __future__ import annotations

from pyspark.sql import DataFrame, SparkSession

from airbnb import bronze, features, gold, io, silver
from airbnb.config import CityConfig
from airbnb.ingest import ensure_raw_file
from airbnb.paths import BRONZE, GOLD_CITY, GOLD_FEATURES, GOLD_NEIGH, SILVER


def check_silver(df: DataFrame) -> None:
    """Fail loudly instead of writing listings that cannot be split, joined or scored."""
    total = df.count()
    missing = df.filter("id IS NULL").count()
    if missing:
        raise ValueError(f"{missing} of {total} listings have no id after parsing; check the id column / cast")


def run_city_etl(
    spark: SparkSession,
    c: CityConfig,
    volume_root: str,
    mode: str,
    stages: tuple[str, ...] = ("bronze", "silver", "gold", "features"),
) -> dict[str, int]:
    counts: dict[str, int] = {}
    if "bronze" in stages:
        path = ensure_raw_file(c, volume_root)
        io.write_city(bronze.read_raw(spark, path, c), BRONZE, c.name, mode)
        counts["bronze"] = io.read_table(spark, BRONZE, mode).filter(f"city = '{c.name}'").count()
    if "silver" in stages:
        b = io.read_table(spark, BRONZE, mode).filter(f"city = '{c.name}'")
        s_df = silver.to_silver(b)
        check_silver(s_df)
        io.write_city(s_df, SILVER, c.name, mode)
        counts["silver"] = io.read_table(spark, SILVER, mode).filter(f"city = '{c.name}'").count()
    if "gold" in stages or "features" in stages:
        s = io.read_table(spark, SILVER, mode).filter(f"city = '{c.name}'")
    if "gold" in stages:
        io.write_city(gold.city_metrics(s), GOLD_CITY, c.name, mode)
        io.write_city(gold.neighbourhood_metrics(s), GOLD_NEIGH, c.name, mode)
        counts["gold_city"] = io.read_table(spark, GOLD_CITY, mode).filter(f"city = '{c.name}'").count()
        counts["gold_neighbourhood"] = io.read_table(spark, GOLD_NEIGH, mode).filter(f"city = '{c.name}'").count()
    if "features" in stages:
        io.write_city(features.build_features(s, c), GOLD_FEATURES, c.name, mode)
        counts["features"] = io.read_table(spark, GOLD_FEATURES, mode).filter(f"city = '{c.name}'").count()
    return counts
