"""Build dashboards/airbnb_spain.lvdash.json (AI/BI dashboard) from dashboards/datasets.sql.

Titles state findings; the numbers in them come from the week-1 run (reports/week1_metrics.md).
Usage: uv run python scripts/build_dashboard.py
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def datasets():
    out, name, buf = [], None, []
    for line in (ROOT / "dashboards" / "datasets.sql").read_text().splitlines():
        m = re.match(r"--\s*name:\s*(\w+)", line)
        if m:
            name, buf = m.group(1), []
        elif line.strip() and not line.startswith("--"):
            buf.append(line)
            if line.rstrip().endswith(";"):
                text = "\n".join(buf).rstrip(";")
                out.append({"name": name, "displayName": name, "queryLines": [ln + "\n" for ln in text.splitlines()]})
    return out


_n = 0


def _wid(prefix):
    global _n
    _n += 1
    return f"{prefix}_{_n}"


def text(md, x, y, w=6, h=2):
    return {"widget": {"name": _wid("text"), "multilineTextboxSpec": {"lines": md.splitlines(keepends=True)}},
            "position": {"x": x, "y": y, "width": w, "height": h}}


def _field(f):
    """'city' -> plain field; ('median', 'price') -> aggregated field."""
    if isinstance(f, str):
        return {"name": f, "expression": f"`{f}`"}
    agg, col = f
    return {"name": f"{agg}({col})", "expression": f"{agg.upper()}(`{col}`)"}


def _fname(f):
    return f if isinstance(f, str) else f"{f[0]}({f[1]})"


def chart(kind, ds, title, x, y, pos, color=None, horizontal=False, group=False, xlabel=None, ylabel=None):
    fields = [x, y] + ([color] if color else [])
    aggregated = any(not isinstance(f, str) for f in fields)
    xs = {"type": "quantitative" if (horizontal or kind == "scatter") else "categorical"}
    ys = {"type": "categorical" if horizontal else "quantitative"}
    enc = {
        "x": {"fieldName": _fname(x), "scale": xs, "displayName": xlabel or _fname(x)},
        "y": {"fieldName": _fname(y), "scale": ys, "displayName": ylabel or _fname(y)},
    }
    if color:
        enc["color"] = {"fieldName": _fname(color), "scale": {"type": "categorical"}, "displayName": _fname(color)}
    spec = {"version": 3, "widgetType": kind, "encodings": enc, "frame": {"showTitle": True, "title": title}}
    if group:
        spec["mark"] = {"layout": "group"}
    return {
        "widget": {
            "name": _wid(kind),
            "queries": [{"name": "main_query", "query": {"datasetName": ds, "fields": [_field(f) for f in fields],
                                                         "disaggregated": not aggregated}}],
            "spec": spec,
        },
        "position": dict(zip(["x", "y", "width", "height"], pos)),
    }


def table(ds, title, cols, pos):
    return {
        "widget": {
            "name": _wid("table"),
            "queries": [{"name": "main_query", "query": {"datasetName": ds, "fields": [_field(c) for c in cols],
                                                         "disaggregated": True}}],
            "spec": {"version": 2, "widgetType": "table",
                     "encodings": {"columns": [{"fieldName": c, "displayName": c} for c in cols]},
                     "frame": {"showTitle": True, "title": title}},
        },
        "position": dict(zip(["x", "y", "width", "height"], pos)),
    }


overview = [
    text("# Madrid has 2.8x more listings than Sevilla, but a typical night costs about the same: EUR 151 vs EUR 158\n"
         "Inside Airbnb snapshots: Madrid 2026-09-17, Sevilla 2026-09-25. Prices in EUR per night.", 0, 0),
    chart("bar", "city_metrics", "Listings per city", "city", ("sum", "listings"), (0, 2, 2, 5)),
    chart("bar", "city_metrics", "Median nightly price (EUR)", "city", ("max", "median_price"), (2, 2, 2, 5)),
    chart("bar", "city_metrics", "Hosts per city", "city", ("sum", "hosts"), (4, 2, 2, 5)),
    chart("bar", "room_mix", "Room-type mix (share of listings)", "city", ("sum", "share"), (0, 7, 2, 6), color="room_type"),
    chart("bar", "city_metrics", "Average days available in the next 365", "city", ("max", "avg_availability_365"), (2, 7, 2, 6)),
    chart("bar", "city_metrics", "Average review score (0-5)", "city", ("max", "avg_review_score"), (4, 7, 2, 6)),
    chart("bar", "top_neighbourhoods", "Most expensive neighbourhoods (median EUR, >= 20 priced listings)",
          ("max", "median_price"), "neighbourhood", (0, 13, 6, 9), color="city", horizontal=True),
]
compare = [
    text("# Same price level, different market: 29% of Madrid listings are private rooms and 12% are mid-term "
         "rentals; Sevilla is 86% entire homes\nPrices: listings between EUR 10 and EUR 1000 (99% of priced listings).", 0, 0),
    chart("bar", "listings_ok", "Median price by room type (EUR)", "room_type", ("median", "price"), (0, 2, 3, 6),
          color="city", group=True),
    chart("line", "listings_ok", "Median price by number of guests (EUR)", "accommodates", ("median", "price"), (3, 2, 3, 6),
          color="city"),
    chart("bar", "listings_ok", "Mid-term (30+ night) rentals are much cheaper per night", "stay_type", ("median", "price"),
          (0, 8, 3, 6), color="city", group=True),
    chart("bar", "city_metrics", "Share of listings with a registered licence", "city", ("max", "share_registered_license"),
          (3, 8, 3, 6)),
]
model = [
    text("# A quarter better than the baseline at home; Barcelona needed its own data (MAE EUR 81 -> 48)\n"
         "Test set: 20% of listings per city, never used for training or model choice. Baseline = median price for the same "
         "room type and number of guests. Charts use test listings priced EUR 10-1000 (99% of priced listings); "
         "on all priced listings, outliers included, the MAE is EUR 68 vs EUR 85.", 0, 0),
    chart("bar", "model_vs_baseline", "MAE on the test set (EUR, lower is better)", "city", ("max", "mae"), (0, 2, 3, 6),
          color="predictor", group=True),
    chart("scatter", "test_predictions", "Predicted vs actual price (test set)", "price", "predicted_price", (3, 2, 3, 6),
          color="city"),
    chart("bar", "test_predictions", "Average error by room type (EUR, < 0 = under-priced)", "room_type", ("avg", "error"),
          (0, 8, 3, 6), color="city", group=True),
    chart("bar", "underpriced_neighbourhoods", "Neighbourhoods the model under-prices most (avg error, EUR)",
          ("max", "avg_error"), "neighbourhood", (3, 8, 3, 6), color="city", horizontal=True),
    chart("bar", "city_c_runs", "Barcelona (new client): test MAE before and after the model change, EUR", "stage", ("max", "mae"),
          (0, 22, 6, 6), color="predictor", group=True),
    table("worst_predictions", "Largest errors on the test set",
          ["city", "neighbourhood", "room_type", "accommodates", "price", "predicted", "error", "direction"], (0, 14, 6, 8)),
]

dash = {
    "datasets": datasets(),
    "pages": [
        {"name": "overview", "displayName": "City overview", "layout": overview, "pageType": "PAGE_TYPE_CANVAS"},
        {"name": "compare", "displayName": "Madrid vs Sevilla", "layout": compare, "pageType": "PAGE_TYPE_CANVAS"},
        {"name": "model", "displayName": "Model", "layout": model, "pageType": "PAGE_TYPE_CANVAS"},
    ],
}
out = ROOT / "dashboards" / "airbnb_spain.lvdash.json"
out.write_text(json.dumps(dash, indent=2, ensure_ascii=False))
print("written", out.relative_to(ROOT), "datasets:", len(dash["datasets"]), "widgets:", sum(len(p["layout"]) for p in dash["pages"]))
