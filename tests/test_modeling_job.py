import gzip
from pathlib import Path

from airbnb.io import read_table
from airbnb.modeling_job import run_score, run_train
from airbnb.paths import GOLD_METRICS, GOLD_PRED
from airbnb.pipeline import run_city_etl

FIXTURE = Path(__file__).parent / "fixtures" / "listings_small.csv"


def test_train_then_score_writes_predictions_and_metrics(spark, tmp_path, monkeypatch, madrid):
    monkeypatch.setenv("AIRBNB_LOCAL_LAKE", str(tmp_path / "lake"))
    raw = tmp_path / "raw" / "madrid" / "2026-09-17" / "listings.csv.gz"
    raw.parent.mkdir(parents=True)
    raw.write_bytes(gzip.compress(FIXTURE.read_bytes()))
    run_city_etl(spark, madrid, str(tmp_path / "raw"), mode="local")

    info = run_train(spark, mode="local", train_cities=["madrid"], folds=2)
    assert info["model_version"] == "local"
    run_score(spark, "madrid", mode="local", train_cities=["madrid"])

    pred = read_table(spark, GOLD_PRED, "local").toPandas()
    assert len(pred) == 6 and pred.predicted_price.notna().all()
    metrics = read_table(spark, GOLD_METRICS, "local").toPandas()
    assert "madrid" in set(metrics.city)


def test_unseen_category_shares():
    import pandas as pd

    from airbnb.modeling_job import unseen_category_shares

    train = pd.DataFrame({"neighbourhood": ["Sol", "Sol", "Goya"], "room_type": ["A", "B", "A"]})
    new = pd.DataFrame({"neighbourhood": ["el Raval", "Sol", "el Born", None], "room_type": ["A", "A", "B", "A"]})
    shares = unseen_category_shares(train, new, ["neighbourhood", "room_type"])
    assert shares == {"unseen_neighbourhood_share": 0.5, "unseen_room_type_share": 0.0}


def test_score_records_unseen_shares(spark, tmp_path, monkeypatch, madrid):
    """Scoring a city whose neighbourhoods the model never saw must be visible in model_metrics."""
    monkeypatch.setenv("AIRBNB_LOCAL_LAKE", str(tmp_path / "lake"))
    raw = tmp_path / "raw" / "madrid" / "2026-09-17" / "listings.csv.gz"
    raw.parent.mkdir(parents=True)
    raw.write_bytes(gzip.compress(FIXTURE.read_bytes()))
    run_city_etl(spark, madrid, str(tmp_path / "raw"), mode="local")
    run_train(spark, mode="local", train_cities=["madrid"], folds=2)
    m = run_score(spark, "madrid", mode="local", train_cities=["madrid"])
    assert "unseen_neighbourhood_share" in m.columns
    assert (m["unseen_neighbourhood_share"] == 0.0).all()
