from pathlib import Path

import pytest

from airbnb.bronze import read_raw
from airbnb.silver import parse_bathrooms, parse_price, to_silver

FIXTURE = str(Path(__file__).parent / "fixtures" / "listings_small.csv")


@pytest.fixture
def silver(spark, madrid):
    return to_silver(read_raw(spark, FIXTURE, madrid))


def test_parse_price_values(spark):
    df = spark.createDataFrame([("",), ("$1,234.00",), ("$0.00",), (None,), ("$65.00",)], "p string")
    got = [r[0] for r in df.select(parse_price(df.p)).collect()]
    assert got == [None, 1234.0, 0.0, None, 65.0]


def test_parse_bathrooms(spark):
    df = spark.createDataFrame([("1.5 shared baths",), ("Half-bath",), ("",), ("2 baths",), ("Shared half-bath",)], "t string")
    got = [tuple(r) for r in df.select(*parse_bathrooms(df.t)).collect()]
    assert got == [(1.5, True), (0.5, False), (None, None), (2.0, False), (0.5, True)]


def test_silver_drops_nothing(silver):
    assert silver.count() == 6


def test_silver_types_and_flags(silver):
    rows = {r.id: r for r in silver.collect()}
    assert rows[2].price == 1234.0 and rows[2].bathrooms == 1.5 and rows[2].bathrooms_shared is True
    assert rows[3].price is None and rows[3].price_missing is True and rows[3].has_license is False
    assert rows[1].host_is_superhost is False and rows[5].host_is_superhost is True
    assert rows[1].amenities_count == 3 and rows[6].amenities_count == 0
    assert rows[1].leak_estimated_revenue_l365d == 9000.0
    assert "price_quote_price_per_night" not in silver.columns


def test_outlier_class_zero_price(silver):
    rows = {r.id: r.outlier_class for r in silver.collect()}
    assert rows[4] == "zero_or_tiny"
    assert rows[1] == "ok"
    assert rows[3] == "no_price"


def test_license_class(spark):
    from airbnb.silver import license_class

    df = spark.createDataFrame([("VT-123",), ("Exempt",), ("En proceso",), ("",), (None,)], "l string")
    got = [r[0] for r in df.select(license_class(df.l)).collect()]
    assert got == ["registered", "exempt", "pending", "none", "none"]


def test_silver_has_host_years(silver):
    assert dict(silver.dtypes)["host_years"] == "int"
    assert dict(silver.dtypes)["license_class"] == "string"
