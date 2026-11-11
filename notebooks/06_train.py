# Databricks notebook source
# MAGIC %md
# MAGIC # Train the price model on the training cities and register it as `workspace.airbnb_gold.price_model@prod`
# MAGIC Model choice (HGB vs Ridge) uses 5-fold CV on the training split only; the test split is touched once, for the report.

# COMMAND ----------

# MAGIC %pip install -q -r ../requirements-databricks.txt

# COMMAND ----------

# Make src/ importable: the repo root is the parent of this notebooks/ folder.
import json, os, sys
REPO = os.path.dirname(os.getcwd()) if os.path.basename(os.getcwd()) == "notebooks" else os.getcwd()
sys.path.insert(0, os.path.join(REPO, "src"))
print("repo:", REPO)

# COMMAND ----------

from airbnb.modeling_job import run_train

dbutils.widgets.text("train_cities", '["madrid", "sevilla"]')
train_cities = json.loads(dbutils.widgets.get("train_cities"))
info = run_train(spark, mode="delta", train_cities=train_cities)
print("model version:", info["model_version"])
print("CV MAE on training rows (EUR):", {k: v for k, v in info["cv"].items()})

# COMMAND ----------

display(info["metrics"].round(2))
