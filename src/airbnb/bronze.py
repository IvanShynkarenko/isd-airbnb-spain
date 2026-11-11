"""Bronze: the raw CSV as-is (every column a string) plus lineage columns."""
from __future__ import annotations

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from airbnb.config import CityConfig


def read_raw(spark: SparkSession, path: str, c: CityConfig) -> DataFrame:
    df = (
        spark.read.option("header", True)
        .option("multiLine", True)  # descriptions contain line breaks
        .option("quote", '"')
        .option("escape", '"')  # quotes inside fields are doubled ("")
        .option("inferSchema", False)
        .option("encoding", "UTF-8")
        .csv(path)
    )
    return df.select(
        "*",
        F.lit(c.name).alias("city"),
        F.to_date(F.lit(c.snapshot)).alias("snapshot_date"),
        F.col("_metadata.file_path").alias("source_file"),
        F.current_timestamp().alias("ingested_at"),
    )
