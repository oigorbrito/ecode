from __future__ import annotations

from typing import Any, Mapping, Sequence

from .contracts import AgentVersion, EvaluationResult


class RandomParentSelector:
    def select(self, versions, results, *, rng: Any) -> AgentVersion:
        if not versions:
            raise ValueError("cannot select a parent from an empty archive")
        return rng.choice(list(versions))


class BestScoreParentSelector:
    """Select by observed score; selection is not acceptance or promotion."""

    def select(
        self,
        versions: Sequence[AgentVersion],
        results: Mapping[str, EvaluationResult],
        *,
        rng: Any,
    ) -> AgentVersion:
        if not versions:
            raise ValueError("cannot select a parent from an empty archive")
        return max(
            versions,
            key=lambda version: (
                results[version.version_id].score
                if results[version.version_id].score is not None
                else float("-inf"),
                version.version_id,
            ),
        )
