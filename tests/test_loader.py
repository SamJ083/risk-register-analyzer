"""Tests for the loader's failure paths and type handling.

Each test writes a small CSV to a temporary folder, so these tests do
not depend on data/risk_register.csv.
"""

import pandas as pd
import pytest

from src import config
from src.loader import load_register

HEADER = ",".join(config.REQUIRED_COLUMNS)
GOOD_ROW = (
    'RISK-001,"Test risk",Access Control,Priya Nair,'
    "4,4,16,2,3,6,Mitigate,In Progress,2027-01-31,2026-10-15"
)


def _write(tmp_path, *lines, header=HEADER):
    path = tmp_path / "register.csv"
    path.write_text("\n".join([header, *lines]) + "\n", encoding="utf-8")
    return path


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_register(tmp_path / "nope.csv")


def test_missing_required_column_raises(tmp_path):
    header = HEADER.replace("owner,", "")
    row = GOOD_ROW.replace("Priya Nair,", "")
    path = _write(tmp_path, row, header=header)
    with pytest.raises(ValueError, match="owner"):
        load_register(path)


def test_non_numeric_score_becomes_blank(tmp_path):
    row = GOOD_ROW.replace("Priya Nair,4,4,16", "Priya Nair,abc,4,16")
    df = load_register(_write(tmp_path, row))
    assert df["likelihood"].isna().all()
    assert df["impact"].iloc[0] == 4


def test_non_integer_score_is_preserved(tmp_path):
    row = GOOD_ROW.replace("Priya Nair,4,4,16", "Priya Nair,4,3.5,14")
    df = load_register(_write(tmp_path, row))
    assert df["impact"].iloc[0] == 3.5


def test_bad_date_becomes_blank(tmp_path):
    row = GOOD_ROW.replace("2027-01-31", "31/01/2027")
    df = load_register(_write(tmp_path, row))
    assert df["treatment_due_date"].isna().all()
    assert df["last_review_date"].iloc[0] == pd.Timestamp("2026-10-15")


def test_whitespace_only_owner_becomes_blank(tmp_path):
    row = GOOD_ROW.replace("Priya Nair", "   ")
    df = load_register(_write(tmp_path, row))
    assert df["owner"].isna().all()


def test_extra_columns_dropped_and_line_numbers_added(tmp_path):
    row_two = GOOD_ROW.replace("RISK-001", "RISK-002")
    path = _write(
        tmp_path,
        GOOD_ROW + ",extra note",
        row_two + ",another note",
        header=HEADER + ",notes",
    )
    df = load_register(path)
    assert list(df.columns) == ["csv_line"] + config.REQUIRED_COLUMNS
    assert list(df["csv_line"]) == [2, 3]