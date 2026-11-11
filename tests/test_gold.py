from pathlib import Path

from airbnb.bronze import read_raw
from airbnb.gold import city_metrics, neighbourhood_metrics
from airbnb.silver import to_silver

FIXTURE = str(Path(__file__).parent / "fixtures" / "listings_small.csv")


def test_city_metrics_one_row_per_city(spark, madrid):
    m = city_metrics(to_silver(read_raw(spark, FIXTURE, madrid))).collect()
    assert len(m) == 1
    r = m[0]
    assert r.city == "madrid" and r.listings == 6 and r.listings_with_price == 5
    assert r.median_price == 90.0  # prices 90, 1234, 0, 25, 300 -> median 90
    assert abs(r.share_entire_home - 4 / 6) < 1e-9


def test_neighbourhood_metrics(spark, madrid):
    m = neighbourhood_metrics(to_silver(read_raw(spark, FIXTURE, madrid))).collect()
    assert [(r.city, r.neighbourhood, r.listings) for r in m] == [("madrid", "Centro", 6)]
