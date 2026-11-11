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
