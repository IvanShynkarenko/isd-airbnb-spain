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
