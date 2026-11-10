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

# Lowest score that counts as High, read from the rating bands.
HIGH_THRESHOLD = dict(config.RATING_BANDS)["High"]


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


def check_residual_exceeds_inherent(df):
    both = df[df["residual_score"].notna() & df["inherent_score"].notna()]
    bad = both[both["residual_score"] > both["inherent_score"]]
    return [
        _finding(row, "residual_exceeds_inherent",
                 f"residual_score {float(row['residual_score']):g} is higher "
                 f"than inherent_score {float(row['inherent_score']):g}")
        for _, row in bad.iterrows()
    ]


def check_overdue_treatment(df):
    as_of = pd.Timestamp(config.AS_OF_DATE)
    open_rows = df[~df["status"].isin(config.CLOSED_STATUSES)]
    due = open_rows["treatment_due_date"]
    overdue = open_rows[due.notna() & (due < as_of)]
    findings = []
    for _, row in overdue.iterrows():
        days = (as_of - row["treatment_due_date"]).days
        findings.append(_finding(
            row, "overdue_treatment",
            f"treatment due {row['treatment_due_date']:%Y-%m-%d} is "
            f"{days} days before {as_of:%Y-%m-%d} and status is {row['status']}"))
    return findings


def check_stale_review(df):
    as_of = pd.Timestamp(config.AS_OF_DATE)
    reviewed = df["last_review_date"]
    age = (as_of - reviewed).dt.days
    stale = df[reviewed.notna() & (age > config.STALE_REVIEW_DAYS)]
    findings = []
    for idx, row in stale.iterrows():
        findings.append(_finding(
            row, "stale_review",
            f"last review {row['last_review_date']:%Y-%m-%d} is "
            f"{int(age[idx])} days before {as_of:%Y-%m-%d} "
            f"(limit {config.STALE_REVIEW_DAYS})"))
    return findings


def _acceptance_score(row):
    """Return (column name, score) used to judge an Accept treatment."""
    if config.ACCEPTANCE_SCORE_BASIS == "inherent":
        return "inherent_score", row["inherent_score"]
    if pd.notna(row["residual_score"]):
        return "residual_score", row["residual_score"]
    return "inherent_score", row["inherent_score"]


def check_high_risk_accepted(df):
    findings = []
    for _, row in df[df["treatment"] == "Accept"].iterrows():
        col, score = _acceptance_score(row)
        if pd.notna(score) and score >= HIGH_THRESHOLD:
            findings.append(_finding(
                row, "high_risk_accepted",
                f"treatment is Accept but {col} {float(score):g} is "
                f"High or above (High starts at {HIGH_THRESHOLD})"))
    return findings


# Add each new check function to this list.
CHECKS = [
    check_duplicate_risk_id,
    check_missing_owner,
    check_score_out_of_range,
    check_non_integer_score,
    check_score_mismatch,
    check_residual_exceeds_inherent,
    check_overdue_treatment,
    check_stale_review,
    check_high_risk_accepted,
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