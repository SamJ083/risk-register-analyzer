"""Data-quality and governance checks for the risk register.

Each check takes the loaded DataFrame and returns a list of finding
dicts. Checks never modify the DataFrame.
"""

import pandas as pd

from src import config

SCORE_INPUTS = ["likelihood", "impact", "residual_likelihood", "residual_impact"]

# (likelihood column, impact column, stated score column)
SCORE_PAIRS = [
    ("likelihood", "impact", "inherent_score"),
    ("residual_likelihood", "residual_impact", "residual_score"),
]


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


def check_score_out_of_range(df):
    findings = []
    for _, row in df.iterrows():
        for col in SCORE_INPUTS:
            value = row[col]
            if pd.isna(value):
                findings.append(_finding(
                    row, "score_out_of_range",
                    f"{col} is missing or non-numeric"))
            elif value < config.SCORE_MIN or value > config.SCORE_MAX:
                findings.append(_finding(
                    row, "score_out_of_range",
                    f"{col} = {float(value):g} is outside "
                    f"{config.SCORE_MIN}-{config.SCORE_MAX}"))
    return findings


def check_non_integer_score(df):
    findings = []
    for _, row in df.iterrows():
        for col in SCORE_INPUTS:
            value = row[col]
            if pd.notna(value) and value != round(value):
                findings.append(_finding(
                    row, "non_integer_score",
                    f"{col} = {float(value):g} is not a whole number"))
    return findings


def check_score_mismatch(df):
    findings = []
    for _, row in df.iterrows():
        for lik, imp, stated in SCORE_PAIRS:
            if pd.isna(row[lik]) or pd.isna(row[imp]):
                continue  # reported by the range check
            expected = row[lik] * row[imp]
            if pd.isna(row[stated]):
                findings.append(_finding(
                    row, "score_mismatch",
                    f"{stated} is missing; {lik} x {imp} = {float(expected):g}"))
            elif row[stated] != expected:
                findings.append(_finding(
                    row, "score_mismatch",
                    f"{stated} is {float(row[stated]):g} but "
                    f"{lik} x {imp} = {float(expected):g}"))
    return findings


# Add each new check function to this list.
CHECKS = [
    check_duplicate_risk_id,
    check_missing_owner,
    check_score_out_of_range,
    check_non_integer_score,
    check_score_mismatch,
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