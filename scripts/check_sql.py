"""Run every dashboard dataset and Genie example query against the local lake (Spark SQL).

Table names workspace.<schema>.<table> are mapped to temp views. Exit code 1 if any query fails.
Usage: uv run python scripts/check_sql.py [--show]
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("PYSPARK_PYTHON", sys.executable)
from pyspark.sql import SparkSession  # noqa: E402

LAKE = Path(os.environ.get("AIRBNB_LOCAL_LAKE", ROOT / "local_lake"))
TABLE_RE = re.compile(r"workspace\.(airbnb_\w+)\.(\w+)")


def blocks(path: Path):
    """Yield (label, sql) for each statement preceded by a '-- name:' or '-- question:' line."""
    label, buf = None, []
    for line in path.read_text().splitlines():
        m = re.match(r"--\s*(name|question):\s*(.+)", line)
        if m:
            label, buf = m.group(2).strip(), []
        elif line.strip() and not line.startswith("--"):
            buf.append(line)
            if line.rstrip().endswith(";"):
                yield label, "\n".join(buf).rstrip(";")
                buf = []


def main() -> int:
    spark = SparkSession.builder.master("local[2]").config("spark.ui.enabled", "false").getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")
    for d in LAKE.iterdir():
        m = TABLE_RE.match(d.name)
        if m and d.is_dir():
            spark.read.parquet(str(d)).createOrReplaceTempView(f"{m.group(1)}__{m.group(2)}")
    failed = 0
    columns = {}
    for f in [ROOT / "dashboards" / "datasets.sql", ROOT / "genie" / "example_questions.sql"]:
        for label, sql in blocks(f):
            try:
                df = spark.sql(TABLE_RE.sub(r"\1__\2", sql))
                rows = df.collect()
                columns[label] = set(df.columns)
                print(f"OK   {f.name}: {label} -> {len(rows)} rows")
                if "--show" in sys.argv or f.name == "example_questions.sql":
                    df.show(10, truncate=False)
            except Exception as e:  # noqa: BLE001
                failed += 1
                print(f"FAIL {f.name}: {label}: {str(e).splitlines()[0]}")
    import json

    dash = json.loads((ROOT / "dashboards" / "airbnb_spain.lvdash.json").read_text())
    for page in dash["pages"]:
        for item in page["layout"]:
            for q in item["widget"].get("queries", []):
                ds = q["query"]["datasetName"]
                if ds not in columns:
                    failed += 1
                    print(f"FAIL widget {item['widget']['name']}: unknown dataset {ds}")
                    continue
                for fld in q["query"]["fields"]:
                    for col in re.findall(r"`(\w+)`", fld["expression"]):
                        if col not in columns[ds]:
                            failed += 1
                            print(f"FAIL widget {item['widget']['name']}: column {col} not in dataset {ds}")
    print("dashboard widgets checked;", "FAILED" if failed else "all OK")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
