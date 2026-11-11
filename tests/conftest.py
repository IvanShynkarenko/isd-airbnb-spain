import os

import pytest


@pytest.fixture(scope="session")
def spark():
    from pyspark.sql import SparkSession

    os.environ.setdefault("PYSPARK_PYTHON", os.sys.executable)
    s = (
        SparkSession.builder.master("local[2]")
        .appName("tests")
        .config("spark.sql.shuffle.partitions", "2")
        .config("spark.ui.enabled", "false")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )
    s.sparkContext.setLogLevel("ERROR")
    yield s
    s.stop()


@pytest.fixture
def madrid():
    from airbnb.config import CityConfig

    return CityConfig("madrid", "spain", "comunidad-de-madrid", "madrid", "2026-09-17", 40.4168, -3.7038)
