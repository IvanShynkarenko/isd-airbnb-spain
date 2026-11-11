from airbnb.features import LEAKAGE_COLUMNS


def test_leakage_list_contains_price_derived_columns():
    for c in ["price_quote_checkin_date", "price_quote_checkout_date", "price_quote_total_price",
              "price_quote_price_per_night", "price_quote_raw", "estimated_revenue_l365d",
              "estimated_occupancy_l365d"]:
        assert c in LEAKAGE_COLUMNS


from pathlib import Path

import pytest

from airbnb.bronze import read_raw
from airbnb.features import CATEGORICAL, FEATURE_COLUMNS, assign_split, build_features, haversine_km
from airbnb.silver import to_silver

FIXTURE = str(Path(__file__).parent / "fixtures" / "listings_small.csv")


def test_split_is_deterministic_and_about_20pct(spark):
    df = spark.range(10000).withColumnRenamed("id", "id")
    a = assign_split(df).filter("split = 'test'").count()
    b = assign_split(df).filter("split = 'test'").count()
    assert a == b
    assert 1800 <= a <= 2200


def test_haversine_madrid_center_zero(spark):
    df = spark.createDataFrame([(40.4168, -3.7038), (40.4168 + 0.009, -3.7038)], "lat double, lon double")
    got = [r[0] for r in df.select(haversine_km("lat", "lon", 40.4168, -3.7038)).collect()]
    assert got[0] == pytest.approx(0.0, abs=1e-9)
    assert got[1] == pytest.approx(1.0, abs=0.01)


@pytest.fixture
def feats(spark, madrid):
    return build_features(to_silver(read_raw(spark, FIXTURE, madrid)), madrid)


def test_build_features_excludes_leakage(feats):
    for c in LEAKAGE_COLUMNS:
        assert c not in feats.columns
        assert f"leak_{c}" not in feats.columns


def test_build_features_has_model_columns_and_flags(feats):
    for c in FEATURE_COLUMNS + CATEGORICAL + ["id", "city", "price", "split", "is_trainable"]:
        assert c in feats.columns, c
    rows = {r.id: r for r in feats.collect()}
    assert rows[1].dist_center_km == pytest.approx(0.0, abs=1e-6)
    assert rows[1].is_trainable is True       # ok price
    assert rows[3].is_trainable is False      # no price
    assert rows[4].is_trainable is False      # zero price
    assert feats.count() == 6                 # every listing kept (predictions for all)
