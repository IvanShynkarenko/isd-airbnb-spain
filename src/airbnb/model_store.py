"""Where the trained model lives: MLflow + Unity Catalog on Databricks, a joblib file locally."""
from __future__ import annotations

import os

import joblib
import pandas as pd

from airbnb.paths import EXPERIMENT, MODEL_ALIAS, MODEL_NAME


def _local_path() -> str:
    return os.path.join(os.environ.get("AIRBNB_LOCAL_LAKE", "local_lake"), "price_model.joblib")


def save_model(pipe, mode: str, sample_X: pd.DataFrame, report: dict) -> str:
    if mode == "local":
        os.makedirs(os.path.dirname(_local_path()), exist_ok=True)
        joblib.dump(pipe, _local_path())
        return "local"
    import mlflow
    from mlflow import MlflowClient
    from mlflow.models import infer_signature

    mlflow.set_registry_uri("databricks-uc")
    mlflow.set_experiment(EXPERIMENT)
    sample = sample_X.head(50).copy()
    with mlflow.start_run(run_name="price_model"):
        mlflow.log_params({"model": report["chosen"], "n_train": report["n_train"]})
        mlflow.log_metrics({f"cv_mae_{k}": report[k] for k in ("hgb", "ridge")})
        info = mlflow.sklearn.log_model(
            pipe,
            "model",
            signature=infer_signature(sample, pipe.predict(sample)),
            registered_model_name=MODEL_NAME,
        )
    client = MlflowClient()
    version = getattr(info, "registered_model_version", None) or max(
        int(v.version) for v in client.search_model_versions(f"name='{MODEL_NAME}'")
    )
    client.set_registered_model_alias(MODEL_NAME, MODEL_ALIAS, str(version))
    return f"v{version}"


def load_model(mode: str):
    """Returns (pipeline, model_version)."""
    if mode == "local":
        return joblib.load(_local_path()), "local"
    import mlflow
    from mlflow import MlflowClient

    mlflow.set_registry_uri("databricks-uc")
    version = MlflowClient().get_model_version_by_alias(MODEL_NAME, MODEL_ALIAS).version
    return mlflow.sklearn.load_model(f"models:/{MODEL_NAME}@{MODEL_ALIAS}"), f"v{version}"
