"""Command-line entry point: load -> check -> score -> report."""

import argparse
import sys
from datetime import datetime
from pathlib import Path

from src import config, report
from src.checks import run_all_checks
from src.loader import load_register
from src.scoring import add_ratings


def _parse_date(text):
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"invalid date '{text}', expected YYYY-MM-DD")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Analyze a risk register CSV and write a findings "
                    "file and a Markdown summary.")
    parser.add_argument(
        "--input", type=Path, default=config.DATA_PATH,
        help="path to the risk register CSV (default: %(default)s)")
    parser.add_argument(
        "--output-dir", type=Path, default=config.OUTPUT_DIR,
        help="folder for findings.csv and summary.md (default: %(default)s)")
    parser.add_argument(
        "--as-of", type=_parse_date, default=config.AS_OF_DATE,
        help="reporting date, YYYY-MM-DD (default: %(default)s)")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    config.AS_OF_DATE = args.as_of  # checks read this at run time

    try:
        df = add_ratings(load_register(args.input))
    except (FileNotFoundError, ValueError) as err:
        print(f"Error: {err}", file=sys.stderr)
        return 2

    findings = run_all_checks(df)
    findings_path = report.write_findings(findings, args.output_dir)
    summary = report.build_summary(df, findings, as_of=args.as_of)
    summary_path = report.write_summary(summary, args.output_dir)

    severity = findings["severity"].value_counts()
    breakdown = ", ".join(
        f"{s} {int(severity.get(s, 0))}" for s in report.SEVERITY_ORDER)
    print(f"Loaded {len(df)} risks from {args.input}")
    print(f"As-of date: {args.as_of:%Y-%m-%d}")
    print(f"Findings: {len(findings)} ({breakdown})")
    print(f"Wrote: {findings_path}")
    print(f"Wrote: {summary_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())