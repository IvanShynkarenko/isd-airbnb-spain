"""City configuration: everything city-specific lives in config/cities.yml."""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote

import yaml

BASE_URL = "https://data.insideairbnb.com"


@dataclass(frozen=True)
class CityConfig:
    name: str
    country: str
    region: str
    city_slug: str
    snapshot: str
    center_lat: float
    center_lon: float


def load_cities(path: str) -> dict[str, CityConfig]:
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)["cities"]
    return {
        name: CityConfig(
            name=name,
            country=str(c["country"]),
            region=str(c["region"]),
            city_slug=str(c["city_slug"]),
            snapshot=str(c["snapshot"]),
            center_lat=float(c["center_lat"]),
            center_lon=float(c["center_lon"]),
        )
        for name, c in raw.items()
    }


def listings_url(c: CityConfig) -> str:
    """URL of the detailed listings file; every path segment is percent-encoded (e.g. andalucía)."""
    segments = [c.country, c.region, c.city_slug, c.snapshot, "data", "listings.csv.gz"]
    return BASE_URL + "/" + "/".join(quote(s, safe="") for s in segments)
