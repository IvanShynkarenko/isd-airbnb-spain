# Databricks notebook source
# MAGIC %md
# MAGIC # Score one city with the production model → `airbnb_gold.predictions` and `airbnb_gold.model_metrics`

# COMMAND ----------

# MAGIC %pip install -q -r ../requirements-databricks.txt

# COMMAND ----------

# Make src/ importable: the repo root is the parent of this notebooks/ folder.
import json, os, sys
REPO = os.path.dirname(os.getcwd()) if os.path.basename(os.getcwd()) == "notebooks" else os.getcwd()
sys.path.insert(0, os.path.join(REPO, "src"))
print("repo:", REPO)

# COMMAND ----------

from airbnb.modeling_job import run_score

dbutils.widgets.text("city", "madrid")
dbutils.widgets.text("train_cities", '["madrid", "sevilla"]')
city = dbutils.widgets.get("city").strip().lower()
metrics = run_score(spark, city, mode="delta", train_cities=json.loads(dbutils.widgets.get("train_cities")))
display(metrics.round(2))
