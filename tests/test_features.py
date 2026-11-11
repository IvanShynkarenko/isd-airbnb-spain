from airbnb.features import LEAKAGE_COLUMNS


def test_leakage_list_contains_price_derived_columns():
    for c in ["price_quote_checkin_date", "price_quote_checkout_date", "price_quote_total_price",
              "price_quote_price_per_night", "price_quote_raw", "estimated_revenue_l365d",
              "estimated_occupancy_l365d"]:
        assert c in LEAKAGE_COLUMNS
