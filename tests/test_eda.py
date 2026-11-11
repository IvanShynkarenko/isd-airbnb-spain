import json
from pathlib import Path

NB = Path(__file__).resolve().parents[1] / "notebooks" / "eda_madrid_sevilla.ipynb"


def _cells():
    return json.loads(NB.read_text())["cells"]


def test_feature_exploration_uses_training_rows_only():
    src = "".join(next(c for c in _cells() if c["cell_type"] == "code" and "amenity (substring)" in "".join(c["source"]))["source"])
    feat_cells = [c for c in _cells() if c["cell_type"] == "code" and "pp = " in "".join(c["source"])]
    assert feat_cells, "section 7 must define its rows (pp)"
    assert 'split == "train"' in "".join(feat_cells[0]["source"])
    assert "patio or balcony" in src and "private patio or balcony" not in src


def test_notebook_executed_without_errors():
    code = [c for c in _cells() if c["cell_type"] == "code"]
    assert all(c.get("outputs") for c in code)
    assert not any(o.get("output_type") == "error" for c in code for o in c["outputs"])
