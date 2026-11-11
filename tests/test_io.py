from airbnb.io import read_table, write_city


def test_write_city_keeps_other_cities(spark, tmp_path, monkeypatch):
    monkeypatch.setenv("AIRBNB_LOCAL_LAKE", str(tmp_path))
    t = "workspace.airbnb_silver.listings"
    write_city(spark.createDataFrame([(1, "madrid")], "id long, city string"), t, "madrid", mode="local")
    write_city(spark.createDataFrame([(2, "sevilla"), (3, "sevilla")], "id long, city string"), t, "sevilla", mode="local")
    write_city(spark.createDataFrame([(4, "madrid")], "id long, city string"), t, "madrid", mode="local")

    rows = sorted((r.id, r.city) for r in read_table(spark, t, mode="local").collect())
    assert rows == [(2, "sevilla"), (3, "sevilla"), (4, "madrid")]
