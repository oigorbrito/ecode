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
        metadata = dict(self.evaluate_fn(agent, context))
        performance = metadata.get("overall_performance") or {}
        artifact_paths = list(metadata.get("artifacts", []))
        artifact_paths.extend(performance.get("files", []))
        artifact_paths.extend(metadata.get("swe_dnames", []))
        artifacts = tuple(
            _artifact_ref(path if Path(path).is_absolute() else context.artifact_dir / path)
            for path in artifact_paths
        )
        if metadata.get("metadata_path"):
            path = Path(metadata["metadata_path"])
            artifacts += (_artifact_ref(path if path.is_absolute() else context.artifact_dir / path),)
        return EvaluationResult(
            evaluation_id=str(metadata.get("evaluation_id", f"{context.run_id}:{agent.version_id}")),
            agent_id=agent.version_id,
            score=performance.get("accuracy_score"),
            status=str(metadata.get("status", "COMPLETED" if performance else "INCOMPLETE")),
            commit_sha=agent.commit_sha,
            source_tree_sha256=agent.source_tree_sha256,
            config_sha256=context.config_sha256,
            model=context.model,
            provider=context.provider,
            benchmark=context.benchmark,
            segment=context.segment,
            artifacts=artifacts,
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
