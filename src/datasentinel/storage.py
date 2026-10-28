"""SQLite persistence for run history."""
import json
import sqlite3

import pandas as pd

SCHEMA = """
CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id INTEGER PRIMARY KEY AUTOINCREMENT, dataset TEXT, status TEXT,
    started_at TEXT, ended_at TEXT, duration_sec REAL, error TEXT);
CREATE TABLE IF NOT EXISTS quality_results (
    run_id INTEGER, total_rows INTEGER, total_columns INTEGER,
    failed_rows INTEGER, score REAL);
CREATE TABLE IF NOT EXISTS validation_issues (
    run_id INTEGER, check_name TEXT, column_name TEXT, severity TEXT,
    count INTEGER, message TEXT);
CREATE TABLE IF NOT EXISTS schema_snapshots (run_id INTEGER, schema_json TEXT);
"""


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    return conn


def save_run(db_path, dataset, status, started, ended, duration, error=None,
             summary=None, issues=None, schema=None) -> int:
    with connect(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO pipeline_runs (dataset,status,started_at,ended_at,duration_sec,error) "
            "VALUES (?,?,?,?,?,?)", (dataset, status, started, ended, duration, error))
        run_id = cur.lastrowid
        if summary:
            conn.execute("INSERT INTO quality_results VALUES (?,?,?,?,?)",
                         (run_id, summary["total_rows"], summary["total_columns"],
                          summary["failed_rows"], summary["score"]))
        for i in issues or []:
            conn.execute("INSERT INTO validation_issues VALUES (?,?,?,?,?,?)",
                         (run_id, i["check"], i["column"], i["severity"], i["count"], i["message"]))
        if schema is not None:
            conn.execute("INSERT INTO schema_snapshots VALUES (?,?)", (run_id, json.dumps(schema)))
    conn.close()
    return run_id


def get_runs(db_path) -> pd.DataFrame:
    conn = connect(db_path)
    df = pd.read_sql_query(
        "SELECT r.run_id, r.dataset, r.status, r.started_at, r.duration_sec, "
        "q.total_rows, q.failed_rows, q.score, r.error FROM pipeline_runs r "
        "LEFT JOIN quality_results q USING(run_id) ORDER BY r.run_id", conn)
    conn.close()
    return df


def get_previous_run(db_path, dataset):
    """Latest successful-execution run for the same dataset: (score, total_rows, schema) or None."""
    conn = connect(db_path)
    row = conn.execute(
        "SELECT q.score, q.total_rows, s.schema_json FROM pipeline_runs r "
        "JOIN quality_results q USING(run_id) JOIN schema_snapshots s USING(run_id) "
        "WHERE r.dataset=? AND r.status!='EXECUTION_FAILED' ORDER BY r.run_id DESC LIMIT 1",
        (dataset,)).fetchone()
    conn.close()
    return None if row is None else {"score": row[0], "total_rows": row[1], "schema": json.loads(row[2])}
