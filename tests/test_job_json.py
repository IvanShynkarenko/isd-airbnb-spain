import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JOB = ROOT / "jobs" / "airbnb_pipeline.json"


def _paths(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "notebook_path":
                yield v
            else:
                yield from _paths(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _paths(v)


def test_job_json_valid():
    text = JOB.read_text()
    assert "barcelona" not in text.lower()
    spec = json.loads(text)
    assert spec["name"] == "airbnb_pipeline"
    params = {p["name"]: p["default"] for p in spec["parameters"]}
    assert json.loads(params["cities"]) == ["madrid", "sevilla"]
    assert params["train"] == "true"
    paths = list(_paths(spec))
    assert len(paths) == 3
    for p in paths:
        assert p.startswith("{REPO}/notebooks/")
        assert (ROOT / (p.replace("{REPO}/", "") + ".py")).exists(), p


def test_notebooks_are_databricks_source_and_thin():
    for nb in (ROOT / "notebooks").glob("*.py"):
        text = nb.read_text()
        assert text.startswith("# Databricks notebook source"), nb.name
        assert not re.search(r"^def |^class ", text, re.M), f"{nb.name} should only call src/airbnb"
