"""Load the risk register CSV and normalise column types.

The loader does not judge data quality. It only makes sure the checks
receive predictable types. Cells that cannot be parsed become blank
(NaN/NaT) so the checks can report them as findings.
"""

from pathlib import Path

import pandas as pd

from src import config

TEXT_COLUMNS = ["risk_id", "title", "category", "owner", "treatment", "status"]
NUMERIC_COLUMNS = [
    "likelihood", "impact", "inherent_score",
    "residual_likelihood", "residual_impact", "residual_score",
]
DATE_COLUMNS = ["treatment_due_date", "last_review_date"]
DATE_FORMAT = "%Y-%m-%d"


def load_register(path=config.DATA_PATH):
    """Read the risk register and return a typed DataFrame."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Risk register not found: {path}")

    raw = pd.read_csv(path, dtype=str)
    raw.columns = raw.columns.str.strip()

    missing = [c for c in config.REQUIRED_COLUMNS if c not in raw.columns]
    if missing:
        raise ValueError(f"Risk register is missing required columns: {missing}")

    df = raw[config.REQUIRED_COLUMNS].copy()

    for col in TEXT_COLUMNS:
        df[col] = df[col].str.strip().replace("", pd.NA)

    for col in NUMERIC_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in DATE_COLUMNS:
        df[col] = pd.to_datetime(df[col], format=DATE_FORMAT, errors="coerce")

    # Line number in the CSV file (header is line 1) for traceable findings.
    df.insert(0, "csv_line", df.index + 2)

    return df