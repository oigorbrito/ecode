from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Callable, Mapping

from ..contracts import AgentVersion, ArtifactRef, EvaluationContext


class ECodeMutationRunner:
    """Adapt ECode's mutation-only operation to the MutationRunner contract.

    The operation and task policy are injected so this adapter does not import
    Docker, model providers, or benchmark packages. The returned candidate hash
    identifies the produced patch artifact; it is not represented as a source
    tree hash.
    """

    def __init__(
        self,
        *,
        mutate_fn: Callable[[AgentVersion, Any, str, str, EvaluationContext], Mapping[str, Any]],
        entry_selector: Callable[[AgentVersion, Any, EvaluationContext], str],
    ):
        self.mutate_fn = mutate_fn
        self.entry_selector = entry_selector

    def mutate(
        self,
        parent: AgentVersion,
        *,
        parent_result,
        child_id: str,
        context: EvaluationContext,
    ) -> AgentVersion:
        entry = self.entry_selector(parent, parent_result, context)
        mutation = self.mutate_fn(parent, parent_result, child_id, entry, context)
        patch_value = mutation.get("model_patch_file")
        if not patch_value:
            raise ValueError("mutation operation did not return a model_patch_file")
        patch_path = Path(patch_value)
        if not patch_path.is_file():
            raise ValueError(f"mutation patch artifact does not exist: {patch_path}")
        digest = hashlib.sha256(patch_path.read_bytes()).hexdigest()
        return AgentVersion(
            version_id=child_id,
            parent_id=parent.version_id,
            commit_sha=context.commit_sha,
            candidate_sha256=digest,
            config_sha256=context.config_sha256,
            artifact=ArtifactRef(str(patch_path.resolve()), digest, "text/x-diff"),
            attributes={"entry": entry, "mutation": dict(mutation)},
        )
