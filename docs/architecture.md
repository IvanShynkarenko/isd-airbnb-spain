# Solution architecture

```mermaid
flowchart LR
  subgraph SRC[Inside Airbnb]
    U["listings.csv.gz<br/>per city, latest snapshot"]
  end
  subgraph RAW["Volume  workspace.airbnb.raw"]
    F["{city}/{snapshot}/listings.csv.gz"]
  end
  subgraph BR["Bronze  airbnb_bronze"]
    B["listings_raw<br/>all columns as text<br/>+ city, snapshot_date,<br/>source_file, ingested_at"]
  end
  subgraph SI["Silver  airbnb_silver"]
    S["listings<br/>typed, cleaned, flags:<br/>price_missing, outlier_class<br/>(no rows dropped)"]
  end
  subgraph GO["Gold  airbnb_gold"]
    G1["city_metrics"]
    G2["neighbourhood_metrics"]
    G3["features<br/>+ split train/test"]
    M[("price_model@prod<br/>Unity Catalog / MLflow")]
    G4["predictions"]
    G5["model_metrics"]
  end
  U -- "download, or manual upload<br/>if egress is blocked" --> F --> B --> S
  S --> G1 & G2 & G3
  G3 -- "train (training cities)" --> M
  M -- "score (any city)" --> G4 & G5
  G1 & G2 & G4 & G5 --> D["AI/BI dashboard"] & GE["Genie Agent"]
```

| layer | what | why |
|---|---|---|
| Volume | the raw file exactly as downloaded, one folder per city and snapshot | reproducible input; works when Free Edition blocks the download (manual upload) |
| Bronze | the CSV read as text plus lineage columns | nothing can fail on types here; we can always re-derive silver |
| Silver | typed and cleaned listings; problems flagged, not dropped | one trustworthy listing table for analysis, dashboard and features |
| Gold | aggregates, model features, predictions and metrics | what the dashboard, Genie and the model consume |

**Job `airbnb_pipeline`** (one definition, city is a parameter):

```
etl_per_city (for each city in `cities`) → should_train? → train (train_cities) → score_per_city (for each city)
   01_etl_city: ingest → bronze → silver → gold metrics → features
```

Every write replaces only the rows of its city (`replaceWhere city = ...`), so cities can be re-run independently.
Adding a city = one entry in `config/cities.yml` + running the job with that city; no code is copied.
