"""Runs one monitored validation and separates EXECUTION failures from QUALITY failures."""
import time
from datetime import datetime

from .loader import load_dataset
from .schema_monitor import compare_schemas, get_schema, has_drift
from .scoring import calculate_score
from .storage import get_previous_run, save_run
from .validators import run_validations

SUCCESS, QUALITY_FAILED, EXECUTION_FAILED = "SUCCESS", "QUALITY_FAILED", "EXECUTION_FAILED"


def run_pipeline(source, rules=None, db_path="datasentinel.db", name=None,
                 row_drop_threshold=0.5, score_drop_threshold=10) -> dict:
    rules = rules or {}
    name = name or str(getattr(source, "name", source))
    started = datetime.now()
    t0 = time.perf_counter()
    result = {"dataset": name, "status": EXECUTION_FAILED, "df": None, "issues": [],
              "summary": None, "alerts": [], "schema_diff": None, "error": None}
    try:
        df = load_dataset(source, filename=name)
        issues = run_validations(df, rules)
        summary = calculate_score(df, issues, rules.get("pass_threshold", 90))
        schema = get_schema(df)
        prev = get_previous_run(db_path, name)
        if prev:
            diff = compare_schemas(prev["schema"], schema)
            result["schema_diff"] = diff
            if has_drift(diff):
                result["alerts"].append(f"Schema drift detected: {diff}")
            if summary["score"] < prev["score"] - score_drop_threshold:
                result["alerts"].append(
                    f"Quality score fell from {prev['score']} to {summary['score']}")
            if summary["total_rows"] < prev["total_rows"] * (1 - row_drop_threshold):
                result["alerts"].append(
                    f"Row count dropped from {prev['total_rows']} to {summary['total_rows']}")
        result.update(df=df, issues=issues, summary=summary,
                      status=SUCCESS if summary["passed"] else QUALITY_FAILED)
    except Exception as exc:  # execution failure: record it, don't crash the app
        result["error"] = f"{type(exc).__name__}: {exc}"
        schema = None

    duration = round(time.perf_counter() - t0, 4)
    result["duration"] = duration
    result["run_id"] = save_run(
        db_path, name, result["status"], started.isoformat(timespec="seconds"),
        datetime.now().isoformat(timespec="seconds"), duration, result["error"],
        result["summary"], result["issues"], schema if result["summary"] else None)
    return result
