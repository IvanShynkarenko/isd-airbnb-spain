import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_model_page_discloses_population_and_unfiltered_mae():
    dash = json.loads((ROOT / "dashboards" / "airbnb_spain.lvdash.json").read_text())
    page = next(p for p in dash["pages"] if p["name"] == "model")
    text = "".join(
        "".join(item["widget"]["multilineTextboxSpec"]["lines"])
        for item in page["layout"] if "multilineTextboxSpec" in item["widget"]
    )
    assert "10-1000" in text and "all priced listings" in text.lower()


def test_table_widgets_use_v2_minimal_column_spec():
    """v1 table specs with displayAs values did not render on Databricks ('Select fields to visualize')."""
    dash = json.loads((ROOT / "dashboards" / "airbnb_spain.lvdash.json").read_text())
    tables = [i["widget"] for p in dash["pages"] for i in p["layout"]
              if i["widget"].get("spec", {}).get("widgetType") == "table"]
    assert tables
    for w in tables:
        assert w["spec"]["version"] == 2
        fields = {f["name"] for f in w["queries"][0]["query"]["fields"]}
        for col in w["spec"]["encodings"]["columns"]:
            assert set(col) == {"fieldName", "displayName"}
            assert col["fieldName"] in fields
