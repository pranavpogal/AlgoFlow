from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.evaluation.core.baseline import (
    DEFAULT_ACCEPTED_BASELINE_PATH,
    BaselineValidationError,
    build_candidate_baseline,
    compare_run_to_baseline,
    human_comparison_summary,
    load_accepted_baseline,
    write_candidate_baseline,
)
from app.evaluation.core.metrics import metric_catalog
from app.evaluation.core.registry import suite_names
from app.evaluation.core.reporting import human_summary
from app.evaluation.core.runner import run_evaluations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.evaluation.cli")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run evaluation suites")
    run_parser.add_argument("--suite", default="all", help="Suite name or all")
    run_parser.add_argument("--split", default=None, help="Optional split filter")
    run_parser.add_argument("--json", action="store_true", help="Write JSON artifacts")
    run_parser.add_argument("--machine", action="store_true", help="Print machine-readable JSON summary")

    compare_parser = subparsers.add_parser("compare", help="Run evals and compare to baseline")
    compare_parser.add_argument("--suite", default="all", help="Suite name or all")
    compare_parser.add_argument("--split", default=None, help="Optional split filter")
    compare_parser.add_argument("--baseline", default=str(DEFAULT_ACCEPTED_BASELINE_PATH))
    compare_parser.add_argument("--json", action="store_true", help="Write run and comparison artifacts")
    compare_parser.add_argument("--machine", action="store_true", help="Print machine-readable comparison JSON")

    baseline_parser = subparsers.add_parser("baseline", help="Accepted-baseline operations")
    baseline_subparsers = baseline_parser.add_subparsers(dest="baseline_command", required=True)
    candidate_parser = baseline_subparsers.add_parser(
        "candidate",
        help="Generate a candidate baseline snapshot without promoting it",
    )
    candidate_parser.add_argument("--suite", default="all", help="Suite name or all")
    candidate_parser.add_argument("--output", required=True, help="Candidate baseline output path")
    candidate_parser.add_argument("--baseline-id", default=None, help="Optional explicit baseline ID")
    candidate_parser.add_argument("--notes", default="Candidate generated from deterministic eval run.")

    subparsers.add_parser("list", help="List registered suites")
    subparsers.add_parser("metrics", help="Print metric catalog")

    args = parser.parse_args(argv)
    try:
        if args.command == "list":
            print("\n".join(suite_names()))
            return 0
        if args.command == "metrics":
            print(json.dumps(metric_catalog(), indent=2))
            return 0
        if args.command == "run":
            result = run_evaluations(suite=args.suite, split=args.split, write_json=args.json)
            if args.machine:
                print(json.dumps(result.to_dict(), indent=2))
            else:
                print(human_summary(result))
            return result.exit_code
        if args.command == "compare":
            result = run_evaluations(suite=args.suite, split=args.split, write_json=args.json)
            baseline = load_accepted_baseline(Path(args.baseline))
            comparison = compare_run_to_baseline(result, baseline)
            _write_comparison_artifact(result.artifact_dir, comparison.to_dict())
            if args.machine:
                print(json.dumps(comparison.to_dict(), indent=2))
            else:
                print(human_summary(result))
                print()
                print(human_comparison_summary(comparison))
            if result.exit_code == 2:
                return 2
            if result.exit_code == 1:
                return 1
            return comparison.exit_code
        if args.command == "baseline" and args.baseline_command == "candidate":
            result = run_evaluations(suite=args.suite)
            if result.exit_code != 0:
                print("Refusing to generate candidate baseline from failing eval run", file=sys.stderr)
                return result.exit_code
            candidate = build_candidate_baseline(
                result,
                baseline_id=args.baseline_id,
                notes=args.notes,
            )
            write_candidate_baseline(candidate, Path(args.output))
            print(f"Wrote candidate baseline: {args.output}")
            return 0
        raise KeyError(f"Unknown command '{args.command}'")
    except BaselineValidationError as exc:
        print(f"Baseline validation failed: {exc}", file=sys.stderr)
        return 2
    except KeyError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except Exception as exc:  # pragma: no cover - final CLI safety boundary
        print(f"Evaluation infrastructure failure: {exc}", file=sys.stderr)
        return 2


def _write_comparison_artifact(artifact_dir: str | None, payload: dict) -> None:
    if not artifact_dir:
        return
    path = Path(artifact_dir) / "baseline_comparison.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
