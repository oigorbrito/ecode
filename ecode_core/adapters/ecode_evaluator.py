from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Callable, Mapping

from ..contracts import AgentVersion, ArtifactRef, EvaluationContext, EvaluationResult


class ECodeEvaluator:
    """Adapt the existing ECode harness/report callback to the Evaluator contract.

    ``evaluate_fn`` owns execution and isolation. This adapter does not invoke a
    provider or execute generated code itself.
    """

    def __init__(self, evaluate_fn: Callable[[AgentVersion, EvaluationContext], Mapping[str, Any]]):
        self.evaluate_fn = evaluate_fn

    def evaluate(self, agent: AgentVersion, context: EvaluationContext) -> EvaluationResult:
        return self.from_metadata(agent, context, self.evaluate_fn(agent, context))

    @staticmethod
    def from_metadata(
        agent: AgentVersion,
        context: EvaluationContext,
        evaluation_metadata: Mapping[str, Any],
    ) -> EvaluationResult:
        """Convert already-persisted ECode metadata without rerunning a harness."""
        metadata = dict(evaluation_metadata)
        performance = metadata.get("overall_performance") or {}
        status = str(metadata.get("status", "COMPLETED" if performance else "INCOMPLETE"))
        artifact_paths = [agent.artifact.path]
        artifact_paths.extend(metadata.get("artifacts", []))
        artifact_paths.extend(performance.get("files", []))
        artifact_paths.extend(metadata.get("swe_dnames", []))
        if metadata.get("metadata_path"):
            artifact_paths.append(metadata["metadata_path"])
        candidate_path = _resolve_artifact_path(Path(agent.artifact.path), context.artifact_dir)
        candidate_ref = _artifact_ref(candidate_path)
        if candidate_ref.sha256 != agent.artifact.sha256:
            raise ValueError(f"candidate artifact changed after registration: {agent.version_id}")
        artifact_refs = {(candidate_ref.path, candidate_ref.sha256): agent.artifact}
        for artifact_path in artifact_paths:
            path = Path(artifact_path)
            resolved = _resolve_artifact_path(path, context.artifact_dir)
            ref = _artifact_ref(resolved)
            artifact_refs.setdefault((ref.path, ref.sha256), ref)
        return EvaluationResult(
            evaluation_id=str(metadata.get("evaluation_id", f"{context.run_id}:{agent.version_id}")),
            agent_id=agent.version_id,
            score=None if status in {"BLOCKED", "INCOMPLETE"} else performance.get("accuracy_score"),
            status=status,
            commit_sha=agent.commit_sha,
            candidate_sha256=agent.candidate_sha256,
            config_sha256=context.config_sha256,
            model=context.model,
            provider=context.provider,
            benchmark=context.benchmark,
            segment=context.segment,
            artifacts=tuple(artifact_refs.values()),
            metadata=metadata,
        )


def _artifact_ref(path: Path) -> ArtifactRef:
    digest = hashlib.sha256()
    if path.is_dir():
        for item in sorted(item for item in path.rglob("*") if item.is_file()):
            relative = item.relative_to(path).as_posix().encode("utf-8")
            content = item.read_bytes()
            digest.update(len(relative).to_bytes(8, "big"))
            digest.update(relative)
            digest.update(len(content).to_bytes(8, "big"))
            digest.update(content)
        media_type = "application/x-directory"
    else:
        digest.update(path.read_bytes())
        media_type = "application/octet-stream"
    return ArtifactRef(path=str(path), sha256=digest.hexdigest(), media_type=media_type)


def _resolve_artifact_path(path: Path, artifact_dir: Path) -> Path:
    if path.is_absolute() or path.exists():
        return path
    return artifact_dir / path
