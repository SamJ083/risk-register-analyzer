"""Write the findings CSV and the Markdown summary report."""

from pathlib import Path

from src import config
from src.scoring import SCORE_PAIRS, heat_map, valid_inputs

SEVERITY_RANK = ["Critical", "High", "Medium", "Low"]
SEVERITY_ORDER = [s for s in SEVERITY_RANK if s in config.SEVERITY.values()]
RATING_ORDER = [label for label, _ in config.RATING_BANDS]


def _md_table(headers, rows):
    """Build a Markdown table from a header list and a list of row tuples."""
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return "\n".join(lines)


def _rating_counts(series):
    counts = series.value_counts()
    rows = [(label, int(counts.get(label, 0))) for label in RATING_ORDER]
    rows.append(("Not rated", int(series.isna().sum())))
    return rows


def _heat_map_md(grid):
    headers = ["Likelihood / Impact"] + [str(c) for c in grid.columns]
    rows = [[idx] + [int(v) for v in grid.loc[idx]] for idx in grid.index]
    return _md_table(headers, rows)


def build_summary(df, findings, as_of=config.AS_OF_DATE):
    """Return the summary report as a Markdown string."""
    lines = [
        "# Risk Register Analysis Summary",
        "",
        f"- As-of date: {as_of:%Y-%m-%d}",
        f"- Risks analyzed: {len(df)}",
        f"- Findings: {len(findings)} across "
        f"{findings['risk_id'].nunique()} distinct risk IDs",
        "",
        "## Findings by severity",
        "",
    ]

    sev_counts = findings["severity"].value_counts()
    lines.append(_md_table(
        ["Severity", "Findings"],
        [(s, int(sev_counts.get(s, 0))) for s in SEVERITY_ORDER]))

    lines += ["", "## Findings by check", ""]
    check_counts = findings["check"].value_counts()
    lines.append(_md_table(
        ["Check", "Severity", "Findings"],
        [(check, sev, int(check_counts.get(check, 0)))
         for check, sev in config.SEVERITY.items()]))

    lines += ["", "## Rating distribution", ""]
    inherent = _rating_counts(df["inherent_rating"])
    residual = _rating_counts(df["residual_rating"])
    lines.append(_md_table(
        ["Rating", "Inherent", "Residual"],
        [(label, i, r) for (label, i), (_, r) in zip(inherent, residual)]))

    for prefix, lik, imp in SCORE_PAIRS:
        grid, excluded = heat_map(df, lik, imp)
        lines += ["", f"## {prefix.capitalize()} heat map", "",
                  _heat_map_md(grid), ""]
        if excluded:
            bad = df[~valid_inputs(df, lik, imp)]
            names = ", ".join(
                f"{row['risk_id']} (line {row['csv_line']})"
                for _, row in bad.iterrows())
            lines.append(
                f"{excluded} risk(s) could not be plotted because likelihood "
                f"or impact is missing, out of range or not a whole number: "
                f"{names}. See findings.csv.")
        else:
            lines.append("All risks could be plotted.")

    bands = ", ".join(f"{label} >= {lowest}" for label, lowest in config.RATING_BANDS)
    lines += [
        "",
        "## Assumptions",
        "",
        "These thresholds are this project's own implementation assumptions, "
        "not requirements from NIST, ISO 27001 or SOC 2.",
        "",
        f"- Rating bands (minimum score): {bands}",
        f"- Stale review: more than {config.STALE_REVIEW_DAYS} days before the as-of date",
        f"- Accept treatments are judged on the {config.ACCEPTANCE_SCORE_BASIS} score",
        f"- Closed or Accepted statuses are never flagged overdue",
        "",
    ]
    return "\n".join(lines)


def write_findings(findings, output_dir=config.OUTPUT_DIR):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "findings.csv"
    findings.to_csv(path, index=False, encoding="utf-8")
    return path


def write_summary(text, output_dir=config.OUTPUT_DIR):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "summary.md"
    path.write_text(text, encoding="utf-8")
    return path