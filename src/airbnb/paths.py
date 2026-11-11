"""Table names and storage locations (single source of truth)."""
from __future__ import annotations

import posixpath

from airbnb.config import CityConfig

CATALOG = "workspace"
VOLUME_ROOT = "/Volumes/workspace/airbnb/raw"

BRONZE = f"{CATALOG}.airbnb_bronze.listings_raw"
SILVER = f"{CATALOG}.airbnb_silver.listings"
GOLD_CITY = f"{CATALOG}.airbnb_gold.city_metrics"
GOLD_NEIGH = f"{CATALOG}.airbnb_gold.neighbourhood_metrics"
GOLD_FEATURES = f"{CATALOG}.airbnb_gold.features"
GOLD_PRED = f"{CATALOG}.airbnb_gold.predictions"
GOLD_METRICS = f"{CATALOG}.airbnb_gold.model_metrics"
MODEL_NAME = f"{CATALOG}.airbnb_gold.price_model"
MODEL_ALIAS = "prod"
EXPERIMENT = "/Shared/isd_airbnb_spain"


def raw_file(volume_root: str, c: CityConfig) -> str:
    return posixpath.join(volume_root, c.name, c.snapshot, "listings.csv.gz")
