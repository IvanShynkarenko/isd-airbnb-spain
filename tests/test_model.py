import numpy as np
import pandas as pd
import pytest

from airbnb.baseline import fit_baseline
from airbnb.features import CATEGORICAL, NUMERIC
from airbnb.model import evaluate, predictions_frame, train


def synthetic(n=3000, seed=0):
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({c: rng.normal(size=n) for c in NUMERIC})
    df["accommodates"] = rng.integers(1, 9, n).astype(float)
    df["dist_center_km"] = rng.uniform(0, 10, n)
    df["room_type"] = rng.choice(["Entire home/apt", "Private room"], n)
    df["property_type"] = rng.choice(["Entire rental unit", "Room in hotel"], n)
    df["neighbourhood"] = rng.choice(["A", "B", "C"], n)
    df["license_class"] = rng.choice(["registered", "none"], n)
    base = np.where(df.room_type == "Entire home/apt", 60, 30)
    df["price"] = (base * df.accommodates * np.exp(-0.08 * df.dist_center_km) * rng.lognormal(0, 0.15, n)).round(2)
    df["id"] = np.arange(n)
    df["city"] = rng.choice(["madrid", "sevilla"], n)
    df["neighbourhood_group"] = "G"
    df["outlier_class"] = "ok"
    df["is_trainable"] = True
    df["split"] = np.where(df.id % 5 == 0, "test", "train")
    return df


@pytest.fixture(scope="module")
def trained():
    df = synthetic()
    tr = df[df.split == "train"]
    pipe, report = train(tr)
    return df, tr, pipe, report


def test_model_beats_baseline_on_synthetic(trained):
    df, tr, pipe, report = trained
    assert report["chosen"] in {"hgb", "ridge"}
    out = predictions_frame(df, pipe, fit_baseline(tr), "test-v")
    m = evaluate(out)
    row = m[(m.city == "all") & (m.population == "ok")].iloc[0]
    assert row.mae_model < 0.7 * row.mae_baseline


def test_evaluate_has_city_and_all_rows(trained):
    df, tr, pipe, _ = trained
    df = df.copy()
    m = evaluate(predictions_frame(df, pipe, fit_baseline(tr), "v"))
    assert set(m.city) == {"madrid", "sevilla", "all"}
    assert set(m.population) == {"ok", "all_priced"}
    for c in ["n", "mae_model", "mae_baseline", "median_ae_model", "mape_model"]:
        assert c in m.columns


def test_predictions_frame_columns_and_no_price_rows(trained):
    df, tr, pipe, _ = trained
    df = df.copy()
    df.loc[df.index[:3], "price"] = np.nan
    df.loc[df.index[:3], "outlier_class"] = "no_price"
    out = predictions_frame(df, pipe, fit_baseline(tr), "v")
    assert len(out) == len(df)
    for c in ["id", "city", "neighbourhood", "room_type", "accommodates", "split", "price", "predicted_price",
              "baseline_price", "error", "abs_error", "model_version", "outlier_class"]:
        assert c in out.columns
    assert (out.loc[out.index[:3], "split"] == "no_price").all()
    assert out.loc[out.index[:3], "error"].isna().all()
    assert out.predicted_price.notna().all()
    r = out.iloc[5]
    assert r.error == pytest.approx(r.predicted_price - r.price)


def test_unseen_category_does_not_crash(trained):
    df, tr, pipe, _ = trained
    df = df.copy()
    new = df.head(5).copy()
    new["neighbourhood"] = "Never seen"
    new["property_type"] = None
    assert np.isfinite(pipe.predict(new[NUMERIC + CATEGORICAL])).all()
