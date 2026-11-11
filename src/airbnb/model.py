"""Price model: gradient boosting on log price (Ridge as the simple comparison), plus evaluation."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.model_selection import KFold, cross_val_score
from sklearn.pipeline import Pipeline, make_pipeline as sk_make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from airbnb.baseline import BaselineModel
from airbnb.features import CATEGORICAL, NUMERIC

INPUT_COLUMNS = NUMERIC + CATEGORICAL
RANDOM_STATE = 42


def _categorical() -> Pipeline:
    return sk_make_pipeline(
        SimpleImputer(strategy="constant", fill_value="missing"),
        OneHotEncoder(handle_unknown="infrequent_if_exist", min_frequency=20, sparse_output=False),
    )


def make_pipeline(kind: str = "hgb") -> TransformedTargetRegressor:
    if kind == "hgb":
        num = SimpleImputer(strategy="median", add_indicator=True)
        reg = HistGradientBoostingRegressor(
            loss="absolute_error",  # median of log price -> median price: what MAE rewards
            learning_rate=0.05,
            max_iter=600,
            max_leaf_nodes=31,
            min_samples_leaf=20,
            random_state=RANDOM_STATE,
        )
    elif kind == "ridge":
        num = sk_make_pipeline(SimpleImputer(strategy="median", add_indicator=True), StandardScaler())
        reg = Ridge(alpha=1.0)
    else:
        raise ValueError(kind)
    pre = ColumnTransformer([("num", num, NUMERIC), ("cat", _categorical(), CATEGORICAL)])
    return TransformedTargetRegressor(
        regressor=Pipeline([("pre", pre), ("reg", reg)]), func=np.log1p, inverse_func=np.expm1
    )


def train(train_pdf: pd.DataFrame, folds: int = 5) -> tuple[TransformedTargetRegressor, dict]:
    """Choose between HGB and Ridge by CV MAE on the training rows only, then refit the winner."""
    t = train_pdf[train_pdf["is_trainable"].astype(bool)]
    X, y = t[INPUT_COLUMNS], t["price"].to_numpy()
    cv = KFold(n_splits=folds, shuffle=True, random_state=RANDOM_STATE)
    report = {
        kind: float(-cross_val_score(make_pipeline(kind), X, y, cv=cv, scoring="neg_mean_absolute_error").mean())
        for kind in ("hgb", "ridge")
    }
    report["chosen"] = min(("hgb", "ridge"), key=lambda k: report[k])
    report["n_train"] = int(len(t))
    pipe = make_pipeline(report["chosen"]).fit(X, y)
    return pipe, report


def predictions_frame(
    pdf: pd.DataFrame, pipe: TransformedTargetRegressor, base: BaselineModel, model_version: str
) -> pd.DataFrame:
    out = pdf[["id", "city", "neighbourhood_group", "neighbourhood", "room_type", "accommodates", "split",
               "outlier_class", "price"]].copy()
    out["split"] = np.where(out["price"].isna(), "no_price", out["split"])
    out["predicted_price"] = pipe.predict(pdf[INPUT_COLUMNS])
    out["baseline_price"] = base.predict(pdf)
    out["error"] = out["predicted_price"] - out["price"]  # < 0 means the model under-prices
    out["abs_error"] = out["error"].abs()
    out["baseline_abs_error"] = (out["baseline_price"] - out["price"]).abs()
    out["model_version"] = model_version
    return out


def _metrics(d: pd.DataFrame) -> dict:
    return {
        "n": int(len(d)),
        "mae_model": float(d["abs_error"].mean()),
        "mae_baseline": float(d["baseline_abs_error"].mean()),
        "median_ae_model": float(d["abs_error"].median()),
        "mape_model": float((d["abs_error"] / d["price"]).mean()),
    }


def evaluate(pred: pd.DataFrame) -> pd.DataFrame:
    """Test-set metrics per city and for all cities together; 'ok' = within price bounds, 'all_priced' = any price."""
    test = pred[pred["split"] == "test"]
    rows = []
    for population, d in (("ok", test[test["outlier_class"] == "ok"]), ("all_priced", test)):
        for city, g in list(d.groupby("city")) + [("all", d)]:
            rows.append({"city": city, "population": population, **_metrics(g)})
    m = pd.DataFrame(rows)
    m["improvement_vs_baseline_pct"] = 100 * (1 - m["mae_model"] / m["mae_baseline"])
    m["model_version"] = pred["model_version"].iloc[0] if len(pred) else None
    return m
