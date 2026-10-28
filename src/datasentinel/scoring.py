"""Quality score = 100 * (1 - failed_rows / total_rows). A row failing many rules counts once."""
from collections import Counter


def calculate_score(df, issues, pass_threshold: float = 90) -> dict:
    total = len(df)
    failed = sorted({r for i in issues for r in i["rows"]})
    score = round(100 * (1 - len(failed) / total), 2) if total else 0.0
    structural = any(i["severity"] == "Critical" for i in issues)
    return {
        "total_rows": total,
        "total_columns": len(df.columns),
        "failed_rows": len(failed),
        "failed_row_index": failed,
        "score": score,
        "severity_counts": dict(Counter(i["severity"] for i in issues)),
        "issue_count": len(issues),
        "passed": score >= pass_threshold and not structural,
    }
