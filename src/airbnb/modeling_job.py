"""Train once on the training cities; score any city with the production model."""
from __future__ import annotations

import pandas as pd
from pyspark.sql import SparkSession

from airbnb import io
from airbnb.baseline import BaselineModel, fit_baseline
from airbnb.features import CATEGORICAL
from airbnb.model import INPUT_COLUMNS, evaluate, predictions_frame, train
from airbnb.model_store import load_model, save_model
from airbnb.paths import GOLD_FEATURES, GOLD_METRICS, GOLD_PRED


def _features(spark: SparkSession, mode: str, cities: list[str]) -> pd.DataFrame:
    quoted = ",".join(f"'{c}'" for c in cities)
    return io.read_table(spark, GOLD_FEATURES, mode).filter(f"city in ({quoted})").toPandas()


def _baseline(train_rows: pd.DataFrame) -> BaselineModel:
    return fit_baseline(train_rows[(train_rows["split"] == "train") & train_rows["is_trainable"].astype(bool)])


def unseen_category_shares(train_rows: pd.DataFrame, new_rows: pd.DataFrame, cols: list[str]) -> dict:
    """Share of rows whose (non-null) category never appeared in the training rows, per column."""
    out = {}
    for c in cols:
        seen = set(train_rows[c].dropna())
        unseen = new_rows[c].notna() & ~new_rows[c].isin(seen)
        out[f"unseen_{c}_share"] = float(unseen.mean()) if len(new_rows) else 0.0
    return out


def _to_spark(spark: SparkSession, pdf: pd.DataFrame):
    return spark.createDataFrame(pdf.astype({c: "object" for c in pdf.columns if pdf[c].dtype == "object"}))


def run_train(spark: SparkSession, mode: str, train_cities: list[str], folds: int = 5) -> dict:
    pdf = _features(spark, mode, train_cities)
    tr = pdf[pdf["split"] == "train"]
    pipe, report = train(tr, folds=folds)
    version = save_model(pipe, mode, tr[INPUT_COLUMNS], report)
    metrics = evaluate(predictions_frame(pdf, pipe, _baseline(pdf), version))
    io.write_city(_to_spark(spark, metrics[metrics["city"] == "all"]), GOLD_METRICS, "all", mode)
    return {"model_version": version, "cv": report, "metrics": metrics}


def run_score(spark: SparkSession, city: str, mode: str, train_cities: list[str]) -> pd.DataFrame:
    pipe, version = load_model(mode)
    train_rows = _features(spark, mode, train_cities)
    train_rows = train_rows[(train_rows["split"] == "train") & train_rows["is_trainable"].astype(bool)]
    city_rows = _features(spark, mode, [city])
    shares = unseen_category_shares(train_rows, city_rows, CATEGORICAL)
    for col, share in shares.items():
        if share > 0.2:
            print(f"WARNING: {city}: {share:.0%} of listings have a {col[7:-6]} the model never saw in training")
    base = _baseline(train_rows)
    pred = predictions_frame(city_rows, pipe, base, version)
    io.write_city(_to_spark(spark, pred), GOLD_PRED, city, mode)
    metrics = evaluate(pred)
    metrics = metrics[metrics["city"] == city].assign(**shares)
    io.write_city(_to_spark(spark, metrics), GOLD_METRICS, city, mode)
    return metrics
