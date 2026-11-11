"""Per-city ETL orchestration shared by Databricks notebooks and the local runner."""
from __future__ import annotations

from pyspark.sql import SparkSession

from airbnb import bronze, io, silver
from airbnb.config import CityConfig
from airbnb.ingest import ensure_raw_file
from airbnb.paths import BRONZE, SILVER


def run_city_etl(
    spark: SparkSession,
    c: CityConfig,
    volume_root: str,
    mode: str,
    stages: tuple[str, ...] = ("bronze", "silver"),
) -> dict[str, int]:
    counts: dict[str, int] = {}
    if "bronze" in stages:
        path = ensure_raw_file(c, volume_root)
        io.write_city(bronze.read_raw(spark, path, c), BRONZE, c.name, mode)
        counts["bronze"] = io.read_table(spark, BRONZE, mode).filter(f"city = '{c.name}'").count()
    if "silver" in stages:
        b = io.read_table(spark, BRONZE, mode).filter(f"city = '{c.name}'")
        io.write_city(silver.to_silver(b), SILVER, c.name, mode)
        counts["silver"] = io.read_table(spark, SILVER, mode).filter(f"city = '{c.name}'").count()
    return counts
