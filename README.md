# Risk Register Analyzer

A Python tool that reads a risk register CSV, runs nine data-quality and governance checks, and writes a findings file plus a Markdown summary with 5x5 heat maps. Built with Pandas only.

All data in this repository is synthetic. The sample register contains deliberately planted defects (and look-alike "decoys" that must not be flagged) so each check can be verified against a known answer.

## Quick start (Windows PowerShell)

```powershell
git clone <repository-url>
cd risk-register-analyzer
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m src.main
pytest -q
```

Tested with Python 3.13 and Pandas 3.1.1. Versions are pinned in `requirements.txt`.

## Usage

```powershell
python -m src.main                                   # defaults from src/config.py
python -m src.main --as-of 2026-12-01                # override the reporting date
python -m src.main --input my_register.csv --output-dir results
```

| Option | Default | Purpose |
|---|---|---|
| `--input` | `data/risk_register.csv` | Risk register CSV to analyze |
| `--output-dir` | `outputs/` | Where `findings.csv` and `summary.md` are written |
| `--as-of` | `2026-11-10` | Reporting date (YYYY-MM-DD) used by the overdue and stale-review checks |

The default as-of date is fixed so results are repeatable. For real use, pass today's date.

Exit codes: `0` on success, `2` if the input file is missing or lacks a required column.

## Input format

The CSV must contain these 14 columns:

`risk_id, title, category, owner, likelihood, impact, inherent_score, residual_likelihood, residual_impact, residual_score, treatment, status, treatment_due_date, last_review_date`

- Likelihood and impact are expected to be whole numbers from 1 to 5.
- `treatment` is one of Mitigate, Accept, Transfer, Avoid. `status` is one of Open, In Progress, Closed, Accepted.
- Dates use ISO format, `YYYY-MM-DD`.
- Cells that cannot be parsed (text in a numeric column, a malformed date) become blank and are reported where a check covers them. Extra columns are ignored.

## Checks

| Check | Flags | Severity |
|---|---|---|
| `duplicate_risk_id` | The same `risk_id` appears on more than one row (every occurrence is flagged) | High |
| `missing_owner` | No owner assigned | Medium |
| `score_out_of_range` | Likelihood or impact (inherent or residual) is outside 1-5, or missing/non-numeric | High |
| `non_integer_score` | Likelihood or impact is in range but not a whole number (e.g. 3.5) | Medium |
| `score_mismatch` | Stated inherent or residual score does not equal likelihood x impact | Medium |
| `residual_exceeds_inherent` | Residual score is higher than inherent score | Medium |
| `overdue_treatment` | Treatment due date is before the as-of date and status is not Closed or Accepted | High |
| `stale_review` | Last review is more than 180 days before the as-of date | Medium |
| `high_risk_accepted` | Treatment is Accept but the score is High or above | High |

## Outputs

- `outputs/findings.csv`: one row per finding (`finding_id, risk_id, check, severity, detail`). Each detail starts with the CSV line number so a reviewer can find the row quickly.
- `outputs/summary.md`: counts by severity and by check (including checks with zero findings), inherent and residual rating distributions, two 5x5 heat maps, and a list of risks that could not be plotted.

Both files in `outputs/` are a committed sample run on the synthetic data: 25 risks, 12 findings (High 6, Medium 6) across 10 distinct risk IDs.

## Assumptions

These thresholds and rules are this project's own implementation assumptions. They are not requirements from NIST, ISO 27001, or SOC 2. All of them live in `src/config.py`.

- **Rating bands** (minimum score): Low 1, Medium 5, High 10, Critical 20. A score is rated by the highest band whose minimum it meets.
- **Stale review:** more than 180 days before the as-of date. Exactly 180 days is not stale.
- **Overdue:** due date strictly before the as-of date, and status is not Closed or Accepted.
- **Heat maps and ratings use likelihood x impact**, not the stated score column, so a mistyped score cannot move a risk to the wrong cell. Risks with invalid likelihood or impact are left off the map and listed in the summary.
- **Accepted risks are judged on the residual score**, falling back to the inherent score if residual is blank. Acceptance is a decision about the exposure that remains after controls. The trade-off is that the tool takes residual scores at face value.
- **Severities** are our own judgment of how urgently each finding type should be looked at.

## Limitations

- The tool checks the register's data, not reality. It cannot verify that controls exist or work, or that a residual score is honest.
- `treatment` and `status` values are not validated yet. A typo such as "Mitigated" passes silently. The allowed values are defined in `config.py` but no check enforces them.
- A blank or malformed date is skipped by the overdue and stale-review checks, not flagged.
- Only the synthetic sample register has been tested.

## Tests

```powershell
pytest -q
```

17 tests. The checks are tested against the answer key for the sample register: the exact list of 12 findings, five decoy rows that must produce nothing, the `--as-of` override, and the residual-versus-inherent setting. The loader tests cover missing files and columns, bad numbers and dates, and blank cells.

## Project layout

```
src/config.py      thresholds, bands, severities, valid values
src/loader.py      CSV loading and type handling
src/checks.py      the nine checks
src/scoring.py     rating labels and heat map counts
src/report.py      findings.csv and summary.md
src/main.py        command-line entry point
data/              synthetic sample register
outputs/           sample run output
tests/             pytest suite
```