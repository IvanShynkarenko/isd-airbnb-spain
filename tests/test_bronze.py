from pathlib import Path

from airbnb.bronze import read_raw

FIXTURE = str(Path(__file__).parent / "fixtures" / "listings_small.csv")


def test_bronze_row_count_with_multiline(spark, madrid):
    df = read_raw(spark, FIXTURE, madrid)
    assert df.count() == 6
    desc = df.filter("id = '2'").select("description").first()[0]
    assert desc == 'Line one\nLine "two" with quotes'


def test_bronze_adds_metadata_and_keeps_strings(spark, madrid):
    df = read_raw(spark, FIXTURE, madrid)
    for c in ["city", "snapshot_date", "source_file", "ingested_at"]:
        assert c in df.columns
    assert dict(df.dtypes)["price"] == "string"
    r = df.select("city", "snapshot_date").first()
    assert r.city == "madrid" and str(r.snapshot_date) == "2026-09-17"
