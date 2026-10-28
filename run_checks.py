"""Command-line runner:  python run_checks.py [data/sales.csv]"""
import json
import sys

from src.datasentinel.pipeline_monitor import run_pipeline
from src.datasentinel.reporting import save_report

path = sys.argv[1] if len(sys.argv) > 1 else "data/sales.csv"
with open("config/rules.json", encoding="utf-8") as f:
    rules = json.load(f)

res = run_pipeline(path, rules)
print(f"Status: {res['status']}  (run #{res['run_id']}, {res['duration']}s)")
if res["error"]:
    sys.exit(f"Execution error: {res['error']}")
s = res["summary"]
print(f"Rows: {s['total_rows']} | Columns: {s['total_columns']} | Failed rows: {s['failed_rows']}")
print(f"Quality score: {s['score']}%  | Issues: {s['issue_count']}")
for i in res["issues"]:
    print(f"[{i['severity']}] {i['check']} | {i['message']}")
for a in res["alerts"]:
    print("ALERT:", a)
print("Report saved:", save_report(res))
