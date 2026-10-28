"""Turn validation results into tables and downloadable reports."""
import json
from datetime import datetime
from pathlib import Path

import pandas as pd

COLUMNS = ["severity", "check", "column", "count", "message"]


def issues_to_df(issues) -> pd.DataFrame:
    return pd.DataFrame([{k: i[k] for k in COLUMNS} for i in issues], columns=COLUMNS)


def failed_rows_df(df, summary) -> pd.DataFrame:
    return df.loc[summary["failed_row_index"]]


def summary_json(result) -> str:
    s = {k: v for k, v in result["summary"].items() if k != "failed_row_index"}
    return json.dumps({"dataset": result["dataset"], "status": result["status"], **s,
                       "alerts": result["alerts"]}, indent=2)


def save_report(result, folder="reports") -> Path:
    Path(folder).mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = Path(folder) / f"report_{Path(result['dataset']).stem}_{stamp}.csv"
    issues_to_df(result["issues"]).to_csv(path, index=False)
    return path
