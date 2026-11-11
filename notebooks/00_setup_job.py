# Databricks notebook source
# MAGIC %md
# MAGIC # Create or update the job `airbnb_pipeline` from `jobs/airbnb_pipeline.json`
# MAGIC Run this once after cloning the repo (and again after pulling changes to the job definition).
# MAGIC It replaces `{REPO}` with this Git folder's path, so the job always runs the notebooks of this folder.

# COMMAND ----------

import json, os
from databricks.sdk import WorkspaceClient

REPO = os.path.dirname(os.getcwd()) if os.path.basename(os.getcwd()) == "notebooks" else os.getcwd()
repo_ws = REPO[len("/Workspace"):] if REPO.startswith("/Workspace/") else REPO
with open(os.path.join(REPO, "jobs", "airbnb_pipeline.json"), encoding="utf-8") as f:
    spec = json.loads(f.read().replace("{REPO}", repo_ws))

w = WorkspaceClient()
existing = w.api_client.do("GET", "/api/2.2/jobs/list", query={"name": spec["name"]}).get("jobs", [])
if existing:
    job_id = existing[0]["job_id"]
    w.api_client.do("POST", "/api/2.2/jobs/reset", body={"job_id": job_id, "new_settings": spec})
    action = "updated"
else:
    job_id = w.api_client.do("POST", "/api/2.2/jobs/create", body=spec)["job_id"]
    action = "created"
print(f"Job {action}: {w.config.host.rstrip('/')}/jobs/{job_id}")
print("Notebooks from:", repo_ws)
