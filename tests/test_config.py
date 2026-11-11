from pathlib import Path

from airbnb.config import CityConfig, listings_url, load_cities

CITIES_YML = Path(__file__).resolve().parents[1] / "config" / "cities.yml"


def test_load_cities_has_training_cities_and_barcelona():
    cities = load_cities(str(CITIES_YML))
    assert set(cities) == {"madrid", "sevilla", "barcelona"}
    assert cities["barcelona"].snapshot == "2026-09-17"
    assert isinstance(cities["madrid"], CityConfig)
    assert cities["madrid"].snapshot == "2026-09-17"
    assert cities["sevilla"].snapshot == "2026-09-25"


def test_listings_url_percent_encodes():
    cities = load_cities(str(CITIES_YML))
    assert listings_url(cities["sevilla"]) == (
        "https://data.insideairbnb.com/spain/andaluc%C3%ADa/sevilla/2026-09-25/data/listings.csv.gz"
    )
    assert listings_url(cities["madrid"]) == (
        "https://data.insideairbnb.com/spain/comunidad-de-madrid/madrid/2026-09-17/data/listings.csv.gz"
    )
