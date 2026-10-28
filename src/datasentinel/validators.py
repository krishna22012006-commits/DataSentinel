"""Validation checks. Every issue records the row positions it affects."""
import pandas as pd

SEVERITY_ORDER = ["Critical", "High", "Medium", "Low"]


def _issue(check, column, severity, rows, message):
    rows = [int(r) for r in rows]
    return {"check": check, "column": column, "severity": severity,
            "count": len(rows), "message": message, "rows": rows}


def check_required_columns(df, columns):
    missing = [c for c in columns if c not in df.columns]
    return [{**_issue("Missing Column", c, "Critical", [], f"Required column '{c}' is absent"),
             "count": 1} for c in missing]


def check_missing_values(df):
    issues = []
    for col in df.columns:
        rows = df.index[df[col].isna()].tolist()
        if rows:
            issues.append(_issue("Missing Values", col, "High", rows,
                                 f"{len(rows)} missing value(s) in {col}"))
    return issues


def check_duplicate_rows(df):
    rows = df.index[df.duplicated()].tolist()
    if not rows:
        return []
    return [_issue("Duplicate Rows", "ALL", "Medium", rows, f"{len(rows)} duplicate row(s) found")]


def check_duplicate_keys(df, columns):
    issues = []
    for col in columns:
        if col in df.columns:
            rows = df.index[df[col].notna() & df[col].duplicated()].tolist()
            if rows:
                issues.append(_issue("Duplicate Key", col, "High", rows,
                                     f"{len(rows)} repeated value(s) in unique column {col}"))
    return issues


def check_negative_values(df, columns):
    issues = []
    for col in columns:
        if col in df.columns:
            nums = pd.to_numeric(df[col], errors="coerce")
            rows = df.index[nums < 0].tolist()
            if rows:
                issues.append(_issue("Negative Values", col, "High", rows,
                                     f"{len(rows)} negative value(s) in {col}"))
    return issues


def check_invalid_numbers(df, columns):
    """Non-numeric text inside a column that should be numeric."""
    issues = []
    for col in columns:
        if col in df.columns:
            bad = pd.to_numeric(df[col], errors="coerce").isna() & df[col].notna()
            rows = df.index[bad].tolist()
            if rows:
                issues.append(_issue("Invalid Type", col, "High", rows,
                                     f"{len(rows)} non-numeric value(s) in {col}"))
    return issues


def check_ranges(df, ranges):
    issues = []
    for col, (low, high) in ranges.items():
        if col in df.columns:
            nums = pd.to_numeric(df[col], errors="coerce")
            rows = df.index[(nums < low) | (nums > high)].tolist()
            if rows:
                issues.append(_issue("Out of Range", col, "Medium", rows,
                                     f"{len(rows)} value(s) in {col} outside [{low}, {high}]"))
    return issues


def run_validations(df: pd.DataFrame, rules: dict | None = None) -> list[dict]:
    """Run all checks. With no rules, only generic checks (nulls, duplicate rows) run."""
    rules = rules or {}
    numeric_cols = list(dict.fromkeys(rules.get("non_negative_columns", [])
                                      + list(rules.get("ranges", {}))))
    issues = []
    issues += check_required_columns(df, rules.get("required_columns", []))
    issues += check_missing_values(df)
    issues += check_duplicate_rows(df)
    issues += check_duplicate_keys(df, rules.get("unique_columns", []))
    issues += check_invalid_numbers(df, numeric_cols)
    issues += check_negative_values(df, rules.get("non_negative_columns", []))
    issues += check_ranges(df, rules.get("ranges", {}))
    issues.sort(key=lambda i: SEVERITY_ORDER.index(i["severity"]))
    return issues
