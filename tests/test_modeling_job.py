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
