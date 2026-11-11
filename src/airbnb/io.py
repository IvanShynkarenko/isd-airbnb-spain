"""Per-city table writes. Re-running one city never touches other cities' rows.

mode="delta": Unity Catalog Delta tables on Databricks (replaceWhere on city).
mode="local": parquet under $AIRBNB_LOCAL_LAKE (default ./local_lake), partitioned by city,
              dynamic partition overwrite - used for local runs and tests.
"""
from __future__ import annotations

import os
import re

from pyspark.sql import DataFrame, SparkSession

_CITY_RE = re.compile(r"^[a-z_]+$")


def _local_dir(table: str) -> str:
    return os.path.join(os.environ.get("AIRBNB_LOCAL_LAKE", "local_lake"), table)


def write_city(df: DataFrame, table: str, city: str, mode: str) -> None:
    if not _CITY_RE.match(city):
        raise ValueError(f"invalid city name: {city!r}")
    if mode == "local":
        df.sparkSession.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")
        df.write.mode("overwrite").partitionBy("city").parquet(_local_dir(table))
    elif mode == "delta":
        spark = df.sparkSession
        catalog, schema, _ = table.split(".")
        spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}")
        writer = df.write.format("delta").mode("overwrite").option("mergeSchema", "true")
        if spark.catalog.tableExists(table):
            writer = writer.option("replaceWhere", f"city = '{city}'")
        writer.saveAsTable(table)
    else:
        raise ValueError(f"unknown mode {mode!r}")


def write_table(df: DataFrame, table: str, mode: str) -> None:
    """Full overwrite (for tables that are not per city)."""
    if mode == "local":
        df.write.mode("overwrite").parquet(_local_dir(table))
    elif mode == "delta":
        catalog, schema, _ = table.split(".")
        df.sparkSession.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}")
        df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(table)
    else:
        raise ValueError(f"unknown mode {mode!r}")


def read_table(spark: SparkSession, table: str, mode: str) -> DataFrame:
    if mode == "local":
        return spark.read.parquet(_local_dir(table))
    if mode == "delta":
        return spark.table(table)
    raise ValueError(f"unknown mode {mode!r}")
