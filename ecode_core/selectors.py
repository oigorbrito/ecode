from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

from .contracts import AgentVersion, EvaluationResult


class RandomParentSelector:
    def select(self, versions, results, *, rng: Any, child_counts=None) -> AgentVersion:
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
        child_counts=None,
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


class DGMWeightedParentSelector:
    """DGM-style score and child-count weighting for single-parent evolution.

    Weight = sigmoid(lambda * (score - alpha_0)) / (1 + valid_child_count).
    Only the versions supplied by the archive's selection-membership policy
    participate. Regression filters, elite/focus selection, and multi-parent
    draws are intentionally outside this initial port.
    """

    def __init__(self, lam: float = 10.0, alpha_0: float = 0.5):
        if not math.isfinite(lam) or lam < 0:
            raise ValueError("lambda must be finite and non-negative")
        if not math.isfinite(alpha_0):
            raise ValueError("alpha_0 must be finite")
        self.lam = lam
        self.alpha_0 = alpha_0

    def select(
        self,
        versions: Sequence[AgentVersion],
        results: Mapping[str, EvaluationResult],
        *,
        rng: Any,
        child_counts: Mapping[str, int] | None = None,
    ) -> AgentVersion:
        eligible = [
            version
            for version in versions
            if version.version_id in results
            and results[version.version_id].score is not None
            and results[version.version_id].status.upper() not in {"BLOCKED", "INCOMPLETE"}
        ]
        if not eligible:
            raise ValueError("cannot select a parent without a scored eligible candidate")

        eligible_ids = {version.version_id for version in eligible}
        observed_child_counts = {version_id: 0 for version_id in eligible_ids}
        if child_counts is None:
            for child in eligible:
                if child.parent_id in observed_child_counts:
                    observed_child_counts[child.parent_id] += 1
        else:
            observed_child_counts.update(
                {version_id: max(0, int(child_counts.get(version_id, 0))) for version_id in eligible_ids}
            )

        weights = []
        for version in eligible:
            score = results[version.version_id].score
            scaled = self.lam * (score - self.alpha_0)
            if scaled >= 0:
                sigmoid = 1.0 / (1.0 + math.exp(-scaled))
            else:
                exp_scaled = math.exp(scaled)
                sigmoid = exp_scaled / (1.0 + exp_scaled)
            weights.append(sigmoid / (1 + observed_child_counts[version.version_id]))

        return rng.choices(eligible, weights=weights, k=1)[0]
