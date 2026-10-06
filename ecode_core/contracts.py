from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional, Protocol, Sequence


@dataclass(frozen=True)
class ArtifactRef:
    path: str
    sha256: str
    media_type: str = "application/octet-stream"


@dataclass(frozen=True)
class AgentVersion:
    version_id: str
    parent_id: Optional[str]
    commit_sha: Optional[str]
    candidate_sha256: str
    config_sha256: str
    artifact: ArtifactRef
    attributes: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EvaluationContext:
    run_id: str
    commit_sha: Optional[str]
    config_sha256: str
    model: str
    provider: str
    benchmark: str
    segment: str
    artifact_dir: Path
    seed: int


@dataclass(frozen=True)
class EvaluationResult:
    evaluation_id: str
    agent_id: str
    score: Optional[float]
    status: str
    commit_sha: Optional[str]
    candidate_sha256: str
    config_sha256: str
    model: str
    provider: str
    benchmark: str
    segment: str
    artifacts: Sequence[ArtifactRef]
    evaluated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        required = {
            "evaluation_id": self.evaluation_id,
            "agent_id": self.agent_id,
            "candidate_sha256": self.candidate_sha256,
            "config_sha256": self.config_sha256,
            "model": self.model,
            "provider": self.provider,
            "benchmark": self.benchmark,
            "segment": self.segment,
            "status": self.status,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise ValueError(f"evaluation provenance fields are required: {', '.join(missing)}")


class ParentSelector(Protocol):
    def select(
        self,
        versions: Sequence[AgentVersion],
        results: Mapping[str, EvaluationResult],
        *,
        rng: Any,
        child_counts: Optional[Mapping[str, int]] = None,
    ) -> AgentVersion: ...


class MutationRunner(Protocol):
    def mutate(
        self,
        parent: AgentVersion,
        *,
        parent_result: EvaluationResult,
        child_id: str,
        context: EvaluationContext,
    ) -> AgentVersion: ...


class Evaluator(Protocol):
    def evaluate(
        self,
        agent: AgentVersion,
        context: EvaluationContext,
    ) -> EvaluationResult: ...


class ArchiveRetentionPolicy(Protocol):
    def retain(self, versions: Sequence[AgentVersion]) -> Sequence[AgentVersion]: ...


class TelemetrySink(Protocol):
    def emit(self, event: Mapping[str, Any]) -> None: ...
