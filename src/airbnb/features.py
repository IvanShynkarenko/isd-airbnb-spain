"""Model features (gold). See notebooks/eda_madrid_sevilla.ipynb section 6 for the leakage review."""
from __future__ import annotations

# Raw columns that must never reach the model: computed from the price, or an outcome of it.
LEAKAGE_COLUMNS = [
    "price_quote_checkin_date",
    "price_quote_checkout_date",
    "price_quote_total_price",
    "price_quote_price_per_night",
    "price_quote_raw",
    "estimated_revenue_l365d",
    "estimated_occupancy_l365d",
    "availability_30",
    "availability_60",
    "availability_90",
    "availability_365",
    "availability_eoy",
    "has_availability",
]
