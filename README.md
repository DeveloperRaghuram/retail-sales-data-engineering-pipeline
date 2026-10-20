# Retail Sales Data Engineering Pipeline

end-to-end batch pipeline using **Python, pandas, SQL, and SQLite**.

## What it does
1. Reads raw retail transactions from `data/raw_sales.csv`.
2. Validates required columns and cleans invalid rows.
3. Standardizes dates, quantities, prices, and text fields.
4. Removes duplicate transaction IDs.
5. Writes clean data to a local SQLite database.
6. Runs SQL analytics and exports results to `output/` as CSV files.

The data is synthetic and created for this project. It contains no company or customer data.

## Architecture
```text
Synthetic raw CSV
      |
      v
Python ingestion + validation
      |
      v
Cleaning + deduplication
      |
      v
SQLite warehouse (sales table)
      |
      v
SQL transformations / analytics
      |
      v
CSV reports in output/
```

## Tech stack
- Python 3.10+
- pandas
- SQLite (built into Python)
- SQL

## Quick start
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
python src/pipeline.py
```

After it runs, inspect:
- `output/clean_sales.csv`
- `output/monthly_revenue.csv`
- `output/revenue_by_category.csv`
- `output/top_products.csv`
- `output/pipeline_summary.json`

## Data quality rules
- Required fields: `transaction_id`, `order_date`, `product`, `category`, `quantity`, `unit_price`, `region`.
- Rows missing required values are rejected.
- Dates must parse successfully.
- Quantity must be greater than zero.
- Unit price must be zero or greater.
- Duplicate transaction IDs keep the first valid occurrence.
- Revenue is calculated as `quantity * unit_price`.

