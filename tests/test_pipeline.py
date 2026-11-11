from pathlib import Path
import gzip

from airbnb.io import read_table
from airbnb.paths import BRONZE, SILVER
from airbnb.pipeline import run_city_etl

FIXTURE = Path(__file__).parent / "fixtures" / "listings_small.csv"


def test_run_city_etl_writes_bronze_and_silver(spark, tmp_path, monkeypatch, madrid):
    monkeypatch.setenv("AIRBNB_LOCAL_LAKE", str(tmp_path / "lake"))
    raw = tmp_path / "raw" / "madrid" / "2026-09-17" / "listings.csv.gz"
    raw.parent.mkdir(parents=True)
    raw.write_bytes(gzip.compress(FIXTURE.read_bytes()))
    counts = run_city_etl(spark, madrid, str(tmp_path / "raw"), mode="local", stages=("bronze", "silver"))
    assert counts == {"bronze": 6, "silver": 6}
    assert read_table(spark, SILVER, "local").filter("city = 'madrid'").count() == 6
    assert read_table(spark, BRONZE, "local").count() == 6


def test_run_city_etl_all_stages(spark, tmp_path, monkeypatch, madrid):
    from airbnb.paths import GOLD_CITY, GOLD_FEATURES, GOLD_NEIGH

    monkeypatch.setenv("AIRBNB_LOCAL_LAKE", str(tmp_path / "lake"))
    raw = tmp_path / "raw" / "madrid" / "2026-09-17" / "listings.csv.gz"
    raw.parent.mkdir(parents=True)
    raw.write_bytes(gzip.compress(FIXTURE.read_bytes()))
    counts = run_city_etl(spark, madrid, str(tmp_path / "raw"), mode="local")
    assert counts == {"bronze": 6, "silver": 6, "gold_city": 1, "gold_neighbourhood": 1, "features": 6}
    assert read_table(spark, GOLD_FEATURES, "local").count() == 6
    assert read_table(spark, GOLD_CITY, "local").count() == 1
    assert read_table(spark, GOLD_NEIGH, "local").count() == 1


def test_check_silver_rejects_null_ids(spark):
    import pytest

    from airbnb.pipeline import check_silver

    good = spark.createDataFrame([(1, "madrid"), (2, "madrid")], "id long, city string")
    check_silver(good)
    bad = spark.createDataFrame([(1, "madrid"), (None, "madrid")], "id long, city string")
    with pytest.raises(ValueError, match="1 of 2 listings have no id"):
        check_silver(bad)
