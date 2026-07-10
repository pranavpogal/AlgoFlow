from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from app.evaluation.core.models import EvalSuiteResult


@dataclass(frozen=True)
class EvalAdapterConfig:
    suite: str
    capability: str
    default_cases_path: Path


class EvalAdapter(ABC):
    config: EvalAdapterConfig

    @abstractmethod
    def run(self, *, cases_path: Path | None = None, split: str | None = None) -> EvalSuiteResult:
        raise NotImplementedError
