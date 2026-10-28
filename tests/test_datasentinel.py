import json
from pathlib import Path

import pandas as pd
import pytest

from src.datasentinel.loader import load_dataset
from src.datasentinel.pipeline_monitor import EXECUTION_FAILED, QUALITY_FAILED, SUCCESS, run_pipeline
from src.datasentinel.schema_monitor import compare_schemas
from src.datasentinel.scoring import calculate_score
from src.datasentinel.validators import run_validations

RULES = json.loads(Path("config/rules.json").read_text())
SALES = "data/sales.csv"


def test_load_ok(tmp_path):
    p = tmp_path / "a.csv"
    p.write_text("id,amount\n1,100\n2,200\n")
    assert len(load_dataset(p)) == 2


def test_load_errors(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_dataset("missing.csv")
    p = tmp_path / "a.txt"
    p.write_text("x")
    with pytest.raises(ValueError):
        load_dataset(p)


def test_sales_issues_detected():
    df = load_dataset(SALES)
    checks = {(i["check"], i["column"]) for i in run_validations(df, RULES)}
    assert ("Missing Values", "amount") in checks
    assert ("Duplicate Key", "transaction_id") in checks
    assert ("Negative Values", "quantity") in checks


def test_duplicate_key_is_not_duplicate_row():
    df = load_dataset(SALES)
    assert not any(i["check"] == "Duplicate Rows" for i in run_validations(df, RULES))


def test_score_counts_row_once():
    df = load_dataset(SALES)
    s = calculate_score(df, run_validations(df, RULES))
    assert s["failed_rows"] == 2  # row 3 fails two rules, row 4 fails one
    assert s["score"] == round(100 * (1 - 2 / 6), 2)


def test_clean_data_scores_100():
    df = pd.DataFrame({"transaction_id": ["A", "B"], "customer": ["x", "y"],
                       "amount": [1, 2], "quantity": [1, 1]})
    assert calculate_score(df, run_validations(df, RULES))["score"] == 100


def test_missing_required_column_is_critical():
    df = pd.DataFrame({"transaction_id": ["A"]})
    assert any(i["severity"] == "Critical" for i in run_validations(df, RULES))


def test_schema_drift():
    d = compare_schemas({"a": "int64", "b": "object"}, {"a": "float64", "c": "int64"})
    assert d["removed"] == ["b"] and d["added"] == ["c"] and "a" in d["type_changed"]


def test_pipeline_statuses_and_history(tmp_path):
    db = str(tmp_path / "t.db")
    assert run_pipeline(SALES, RULES, db)["status"] == QUALITY_FAILED
    assert run_pipeline("nope.csv", RULES, db)["status"] == EXECUTION_FAILED
    good = tmp_path / "good.csv"
    good.write_text("transaction_id,customer,amount,quantity\nA,x,1,1\nB,y,2,1\n")
    assert run_pipeline(str(good), RULES, db)["status"] == SUCCESS


def test_pipeline_flags_schema_drift(tmp_path):
    db = str(tmp_path / "t.db")
    f = tmp_path / "d.csv"
    f.write_text("transaction_id,customer,amount,quantity\nA,x,1,1\n")
    run_pipeline(str(f), RULES, db)
    f.write_text("transaction_id,customer,amount\nA,x,1\n")
    res = run_pipeline(str(f), RULES, db)
    assert any("Schema drift" in a for a in res["alerts"])
