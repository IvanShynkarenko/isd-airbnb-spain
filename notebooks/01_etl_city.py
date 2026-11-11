# Databricks notebook source
# MAGIC %md
# MAGIC # ETL for one city: raw file → bronze → silver → gold metrics → model features
# MAGIC Parameter `city` must exist in `config/cities.yml`. Every write replaces only this city's rows.

# COMMAND ----------

# MAGIC %pip install -q -r ../requirements-databricks.txt

# COMMAND ----------

# Make src/ importable: the repo root is the parent of this notebooks/ folder.
import json, os, sys
REPO = os.path.dirname(os.getcwd()) if os.path.basename(os.getcwd()) == "notebooks" else os.getcwd()
sys.path.insert(0, os.path.join(REPO, "src"))
print("repo:", REPO)

# COMMAND ----------

from airbnb.config import load_cities
from airbnb.paths import VOLUME_ROOT
from airbnb.pipeline import run_city_etl

dbutils.widgets.text("city", "madrid")
dbutils.widgets.text("volume_root", VOLUME_ROOT)
city = dbutils.widgets.get("city").strip().lower()
cities = load_cities(os.path.join(REPO, "config", "cities.yml"))
if city not in cities:
    raise ValueError(f"City '{city}' is not in config/cities.yml (known: {sorted(cities)})")

counts = run_city_etl(spark, cities[city], dbutils.widgets.get("volume_root"), mode="delta")
print(city, counts)

# COMMAND ----------

dbutils.notebook.exit(json.dumps({"city": city, **counts}))
