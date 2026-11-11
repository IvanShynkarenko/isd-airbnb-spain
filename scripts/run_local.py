"""Run the pipeline locally (PySpark + parquet 'lake') on files in data/.

Usage: uv run python scripts/run_local.py [--cities madrid sevilla] [--stage silver|gold|train|score|all]
"""
import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("AIRBNB_LOCAL_LAKE", str(ROOT / "local_lake"))
os.environ.setdefault("PYSPARK_PYTHON", sys.executable)

from pyspark.sql import SparkSession  # noqa: E402

from airbnb.config import load_cities  # noqa: E402
from airbnb.modeling_job import run_score, run_train  # noqa: E402
from airbnb.pipeline import run_city_etl  # noqa: E402

STAGES = ["silver", "gold", "train", "score"]


def spark_session() -> SparkSession:
    s = (
        SparkSession.builder.master("local[4]")
        .appName("isd-airbnb-local")
        .config("spark.driver.memory", "4g")
        .config("spark.sql.shuffle.partitions", "8")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )
    s.sparkContext.setLogLevel("ERROR")
    return s


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cities", nargs="+", default=["madrid", "sevilla"])
    ap.add_argument("--train-cities", nargs="+", default=["madrid", "sevilla"])
    ap.add_argument("--stage", choices=STAGES + ["all"], default="all")
    args = ap.parse_args()
    stages = STAGES if args.stage == "all" else [args.stage]
    cities = load_cities(str(ROOT / "config" / "cities.yml"))
    spark = spark_session()
    volume_root = str(ROOT / "data")
    if "silver" in stages or "gold" in stages:
        for name in args.cities:
            print(name, run_city_etl(spark, cities[name], volume_root, mode="local"))
    if "train" in stages:
        info = run_train(spark, mode="local", train_cities=args.train_cities)
        print("CV MAE on train (EUR):", {k: round(v, 2) if isinstance(v, float) else v for k, v in info["cv"].items()})
    if "score" in stages:
        for name in args.cities:
            print(run_score(spark, name, mode="local", train_cities=args.train_cities).round(2).to_string(index=False))


if __name__ == "__main__":
    main()
