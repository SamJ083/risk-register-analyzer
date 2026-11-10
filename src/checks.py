"""Data-quality and governance checks for the risk register.

Each check takes the loaded DataFrame and returns a list of finding
dicts. Checks never modify the DataFrame.
"""

import pandas as pd

from src import config


def _finding(row, check, detail):
    return {
        "risk_id": row["risk_id"],
        "check": check,
        "severity": config.SEVERITY[check],
        "detail": f"Line {row['csv_line']}: {detail}",
    }


def check_duplicate_risk_id(df):
    ids = df["risk_id"]
    dupes = df[ids.notna() & ids.duplicated(keep=False)]
    return [
        _finding(row, "duplicate_risk_id",
                 f"risk_id {row['risk_id']} appears more than once")
        for _, row in dupes.iterrows()
    ]


def check_missing_owner(df):
    missing = df[df["owner"].isna()]
    return [
        _finding(row, "missing_owner", "no owner assigned")
        for _, row in missing.iterrows()
    ]


# Add each new check function to this list.
CHECKS = [
    check_duplicate_risk_id,
    check_missing_owner,
]

FINDING_COLUMNS = ["risk_id", "check", "severity", "detail"]


def run_all_checks(df):
    """Run every check and return one findings table with sequential IDs."""
    findings = []
    for check in CHECKS:
        findings.extend(check(df))
    result = pd.DataFrame(findings, columns=FINDING_COLUMNS)
    result.insert(0, "finding_id", [f"F-{i:03d}" for i in range(1, len(result) + 1)])
    return result