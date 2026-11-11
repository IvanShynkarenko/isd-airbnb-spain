"""Download raw listings for the configured cities into data/<city>/<snapshot>/listings.csv.gz.

Use this when Databricks cannot reach insideairbnb.com: run it locally, then upload the files to
/Volumes/workspace/airbnb/raw/<city>/<snapshot>/ (see docs/DEPLOY_UA.md).
Usage: uv run python scripts/fetch_data.py [city ...]
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from airbnb.config import load_cities  # noqa: E402
from airbnb.ingest import ensure_raw_file  # noqa: E402

cities = load_cities(str(ROOT / "config" / "cities.yml"))
for name in sys.argv[1:] or list(cities):
    print(name, "->", ensure_raw_file(cities[name], str(ROOT / "data")))
