from pathlib import Path
import json
import sqlite3
from datetime import datetime, timezone

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "raw_sales.csv"
OUTPUT_DIR = ROOT / "output"
DB_PATH = OUTPUT_DIR / "retail_warehouse.db"

REQUIRED_COLUMNS = [
    "transaction_id", "order_date", "product", "category",
    "quantity", "unit_price", "region"
]


def run_pipeline():
    OUTPUT_DIR.mkdir(exist_ok=True)

    # 1. Ingest
    raw = pd.read_csv(DATA_PATH)
    initial_rows = len(raw)

    missing_columns = sorted(set(REQUIRED_COLUMNS) - set(raw.columns))
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    # 2. Normalize and validate
    df = raw.copy()
    for col in ["transaction_id", "product", "category", "region"]:
        df[col] = df[col].astype("string").str.strip()

    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")

    required_present = df[REQUIRED_COLUMNS].notna().all(axis=1)
    valid_date = df["order_date"].notna()
    valid_quantity = df["quantity"].gt(0)
    valid_price = df["unit_price"].ge(0)
    nonempty_strings = (
        df["transaction_id"].ne("")
        & df["product"].ne("")
        & df["category"].ne("")
        & df["region"].ne("")
    )

    valid_mask = (
        required_present & valid_date & valid_quantity
        & valid_price & nonempty_strings
    )

    rejected = df.loc[~valid_mask].copy()
    clean = df.loc[valid_mask].copy()

    before_dedup = len(clean)
    clean = clean.drop_duplicates(subset=["transaction_id"], keep="first")
    duplicate_rows_removed = before_dedup - len(clean)

    clean["quantity"] = clean["quantity"].astype(int)
    clean["unit_price"] = clean["unit_price"].round(2)
    clean["revenue"] = (clean["quantity"] * clean["unit_price"]).round(2)
    clean["order_date"] = clean["order_date"].dt.strftime("%Y-%m-%d")
    clean = clean[REQUIRED_COLUMNS + ["revenue"]].sort_values("order_date")

    # 3. Load into a local relational warehouse
    with sqlite3.connect(DB_PATH) as conn:
        clean.to_sql("sales", conn, if_exists="replace", index=False)

        monthly = pd.read_sql_query(
            """
            SELECT substr(order_date, 1, 7) AS month,
                   ROUND(SUM(revenue), 2) AS revenue,
                   SUM(quantity) AS units_sold,
                   COUNT(*) AS transaction_count
            FROM sales
            GROUP BY substr(order_date, 1, 7)
            ORDER BY month
            """, conn
        )
        category = pd.read_sql_query(
            """
            SELECT category,
                   ROUND(SUM(revenue), 2) AS revenue,
                   SUM(quantity) AS units_sold,
                   COUNT(*) AS transaction_count
            FROM sales
            GROUP BY category
            ORDER BY revenue DESC
            """, conn
        )
        top_products = pd.read_sql_query(
            """
            SELECT product,
                   ROUND(SUM(revenue), 2) AS revenue,
                   SUM(quantity) AS units_sold
            FROM sales
            GROUP BY product
            ORDER BY revenue DESC
            LIMIT 5
            """, conn
        )

    # 4. Export curated outputs
    clean.to_csv(OUTPUT_DIR / "clean_sales.csv", index=False)
    rejected.to_csv(OUTPUT_DIR / "rejected_rows.csv", index=False)
    monthly.to_csv(OUTPUT_DIR / "monthly_revenue.csv", index=False)
    category.to_csv(OUTPUT_DIR / "revenue_by_category.csv", index=False)
    top_products.to_csv(OUTPUT_DIR / "top_products.csv", index=False)

    summary = {
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "source_file": str(DATA_PATH.relative_to(ROOT)),
        "input_rows": int(initial_rows),
        "accepted_rows": int(len(clean)),
        "rejected_rows": int(len(rejected)),
        "duplicate_rows_removed": int(duplicate_rows_removed),
        "total_revenue": round(float(clean["revenue"].sum()), 2),
        "warehouse": str(DB_PATH.relative_to(ROOT)),
    }
    (OUTPUT_DIR / "pipeline_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    print("Pipeline completed successfully.")
    print(json.dumps(summary, indent=2))
    print("\nMonthly revenue:")
    print(monthly.to_string(index=False))
    print("\nRevenue by category:")
    print(category.to_string(index=False))


if __name__ == "__main__":
    run_pipeline()
