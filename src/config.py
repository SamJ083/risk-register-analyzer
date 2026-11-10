"""Configuration for the Risk Register Analyzer.

Every threshold below is this project's own implementation assumption.
None of them is a requirement taken from NIST, ISO 27001, or SOC 2.
"""

from datetime import date
from pathlib import Path

# --- Paths (built from this file's location, so they work on any machine) ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "risk_register.csv"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

# --- Reporting date (fixed so results are repeatable; main.py will allow an override) ---
AS_OF_DATE = date(2026, 11, 10)

# --- Thresholds ---
STALE_REVIEW_DAYS = 180  # a review older than this many days is stale
SCORE_MIN = 1            # valid range for likelihood and impact
SCORE_MAX = 5

# --- Rating bands: (label, lowest score in band), checked from the top down ---
RATING_BANDS = [
    ("Critical", 20),
    ("High", 10),
    ("Medium", 5),
    ("Low", 1),
]

# --- Expected data format ---
REQUIRED_COLUMNS = [
    "risk_id", "title", "category", "owner",
    "likelihood", "impact", "inherent_score",
    "residual_likelihood", "residual_impact", "residual_score",
    "treatment", "status", "treatment_due_date", "last_review_date",
]
VALID_TREATMENTS = ["Mitigate", "Accept", "Transfer", "Avoid"]
VALID_STATUSES = ["Open", "In Progress", "Closed", "Accepted"]

# Statuses where treatment work is finished or deliberately not pursued,
# so a past due date is not an overdue finding.
CLOSED_STATUSES = ["Closed", "Accepted"]

# --- Finding severity per check (our own assumptions, not framework requirements) ---
SEVERITY = {
    "duplicate_risk_id": "High",
    "missing_owner": "Medium",
    "score_out_of_range": "High",
    "non_integer_score": "Medium",
    "score_mismatch": "Medium",
    "residual_exceeds_inherent": "Medium",
    "overdue_treatment": "High",
    "stale_review": "Medium",
    "high_risk_accepted": "High",
}