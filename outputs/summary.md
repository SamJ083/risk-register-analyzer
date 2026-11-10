# Risk Register Analysis Summary

- As-of date: 2026-11-10
- Risks analyzed: 25
- Findings: 12 across 10 distinct risk IDs

## Findings by severity

| Severity | Findings |
| --- | --- |
| High | 6 |
| Medium | 6 |

## Findings by check

| Check | Severity | Findings |
| --- | --- | --- |
| duplicate_risk_id | High | 2 |
| missing_owner | Medium | 2 |
| score_out_of_range | High | 1 |
| non_integer_score | Medium | 1 |
| score_mismatch | Medium | 1 |
| residual_exceeds_inherent | Medium | 1 |
| overdue_treatment | High | 2 |
| stale_review | Medium | 1 |
| high_risk_accepted | High | 1 |

## Rating distribution

| Rating | Inherent | Residual |
| --- | --- | --- |
| Critical | 2 | 0 |
| High | 12 | 4 |
| Medium | 8 | 10 |
| Low | 1 | 11 |
| Not rated | 2 | 0 |

## Inherent heat map

| Likelihood / Impact | 1 | 2 | 3 | 4 | 5 |
| --- | --- | --- | --- | --- | --- |
| 5 | 0 | 0 | 0 | 0 | 1 |
| 4 | 0 | 0 | 1 | 5 | 1 |
| 3 | 0 | 0 | 6 | 4 | 1 |
| 2 | 0 | 1 | 1 | 1 | 1 |
| 1 | 0 | 0 | 0 | 0 | 0 |

2 risk(s) could not be plotted because likelihood or impact is missing, out of range or not a whole number: RISK-007 (line 8), RISK-009 (line 10). See findings.csv.

## Residual heat map

| Likelihood / Impact | 1 | 2 | 3 | 4 | 5 |
| --- | --- | --- | --- | --- | --- |
| 5 | 0 | 0 | 0 | 0 | 0 |
| 4 | 0 | 0 | 2 | 0 | 0 |
| 3 | 0 | 0 | 2 | 2 | 0 |
| 2 | 0 | 5 | 7 | 1 | 0 |
| 1 | 0 | 5 | 1 | 0 | 0 |

All risks could be plotted.

## Assumptions

These thresholds are this project's own implementation assumptions, not requirements from NIST, ISO 27001 or SOC 2.

- Rating bands (minimum score): Critical >= 20, High >= 10, Medium >= 5, Low >= 1
- Stale review: more than 180 days before the as-of date
- Accept treatments are judged on the residual score
- Closed or Accepted statuses are never flagged overdue
