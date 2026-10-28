# DataSentinel 🛡️
Automated data quality and pipeline failure detector (Python, Pandas, Streamlit, Plotly, SQLite, pytest).

## Features
- Load CSV / Excel; validate missing values, duplicate rows, duplicate keys, invalid types, negatives, ranges, required columns
- Quality score: `100 × (1 − failed_rows / total_rows)` (a row failing several rules counts once)
- Rules in `config/rules.json` (editable in the dashboard)
- SQLite run history, schema-drift detection, score-drop and row-drop alerts
- Distinguishes **QUALITY_FAILED** (bad data) from **EXECUTION_FAILED** (pipeline crashed)
- Streamlit dashboard with filters, charts and downloadable reports

## Setup (Windows PowerShell)
```
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Run
```
python -m pytest -q          # tests
python run_checks.py         # CLI on data/sales.csv
streamlit run app.py         # dashboard
```

## Structure
```
app.py  run_checks.py  config/rules.json  data/sales.csv
src/datasentinel/  loader  validators  scoring  schema_monitor  storage  pipeline_monitor  reporting
tests/test_datasentinel.py
```

## Rules format
```json
{"required_columns": [...], "unique_columns": [...], "non_negative_columns": [...],
 "ranges": {"amount": [0, 100000]}, "pass_threshold": 90}
```

## Roadmap
FastAPI endpoints, Docker, scheduled runs, statistical anomaly detection.
