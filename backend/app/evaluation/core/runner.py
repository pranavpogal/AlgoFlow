from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.evaluation.core.models import EvalRunResult, EvalSuiteResult
from app.evaluation.core.registry import selected_adapters
from app.evaluation.core.reporting import write_artifacts

DEFAULT_ARTIFACT_ROOT = Path("../evals/artifacts")


def run_evaluations(
    *,
    suite: str = "all",
    split: str | None = None,
    write_json: bool = False,
    artifact_root: Path = DEFAULT_ARTIFACT_ROOT,
) -> EvalRunResult:
    run_id = f"eval_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{uuid4().hex[:8]}"
    started = datetime.now(UTC).isoformat()
    suite_results: list[EvalSuiteResult] = []
    for adapter in selected_adapters(suite):
        suite_results.append(adapter.run(split=split))
    finished = datetime.now(UTC).isoformat()
    artifact_dir = artifact_root / run_id if write_json else None
    result = EvalRunResult(
        run_id=run_id,
        suites=suite_results,
        artifact_dir=str(artifact_dir) if artifact_dir else None,
        started_at=started,
        finished_at=finished,
    )
    if artifact_dir:
        write_artifacts(result, artifact_dir)
    return result
