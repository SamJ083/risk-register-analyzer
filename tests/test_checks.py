"""Answer-key tests for the synthetic risk register.

These run the real checks against data/risk_register.csv. If the dataset
changes, update EXPECTED to match.
"""

from datetime import date

import pytest

from src import config
from src.checks import run_all_checks
from src.loader import load_register

# (risk_id, check, line number in the CSV, header = line 1)
EXPECTED = sorted([
    ("RISK-004", "missing_owner", 5),
    ("RISK-005", "duplicate_risk_id", 6),
    ("RISK-005", "duplicate_risk_id", 24),
    ("RISK-007", "score_out_of_range", 8),
    ("RISK-009", "non_integer_score", 10),
    ("RISK-010", "score_mismatch", 11),
    ("RISK-013", "residual_exceeds_inherent", 14),
    ("RISK-015", "overdue_treatment", 16),
    ("RISK-017", "stale_review", 18),
    ("RISK-019", "high_risk_accepted", 20),
    ("RISK-025", "missing_owner", 26),
    ("RISK-025", "overdue_treatment", 26),
])

# Look suspicious but are valid: closed with old due date (003, 021),
# low-risk Accept (006), residual equal to inherent (008), review exactly
# 180 days old (018).
DECOYS = ["RISK-003", "RISK-006", "RISK-008", "RISK-018", "RISK-021"]


def _keys(findings):
    return sorted(
        (row.risk_id, row.check, int(row.detail.split(":")[0].removeprefix("Line ")))
        for row in findings.itertuples()
    )


@pytest.fixture(autouse=True)
def fixed_settings(monkeypatch):
    monkeypatch.setattr(config, "AS_OF_DATE", date(2026, 11, 10))
    monkeypatch.setattr(config, "ACCEPTANCE_SCORE_BASIS", "residual")


@pytest.fixture
def findings():
    return run_all_checks(load_register())


def test_total_finding_count(findings):
    assert len(findings) == 12


def test_findings_match_answer_key(findings):
    assert _keys(findings) == EXPECTED


@pytest.mark.parametrize("risk_id", DECOYS)
def test_decoys_produce_no_findings(findings, risk_id):
    assert risk_id not in set(findings["risk_id"])


def test_finding_ids_are_sequential(findings):
    expected_ids = [f"F-{i:03d}" for i in range(1, len(findings) + 1)]
    assert list(findings["finding_id"]) == expected_ids


def test_later_as_of_date_makes_boundary_risk_stale(monkeypatch):
    monkeypatch.setattr(config, "AS_OF_DATE", date(2026, 12, 1))
    result = run_all_checks(load_register())
    assert _keys(result) == sorted(EXPECTED + [("RISK-018", "stale_review", 19)])


def test_inherent_acceptance_basis_gives_same_findings(monkeypatch):
    monkeypatch.setattr(config, "ACCEPTANCE_SCORE_BASIS", "inherent")
    result = run_all_checks(load_register())
    assert _keys(result) == EXPECTED