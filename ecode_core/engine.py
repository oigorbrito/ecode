from __future__ import annotations

import random

from .archive import Archive
from .contracts import (
    AgentVersion,
    EvaluationContext,
    EvaluationResult,
    Evaluator,
    MutationRunner,
    ParentSelector,
    TelemetrySink,
)
from .telemetry import NullTelemetry


class EvolutionEngine:
    def __init__(
        self,
        *,
        archive: Archive,
        parent_selector: ParentSelector,
        mutation_runner: MutationRunner,
        evaluator: Evaluator,
        context: EvaluationContext,
        telemetry: TelemetrySink | None = None,
    ):
        self.archive = archive
        self.parent_selector = parent_selector
        self.mutation_runner = mutation_runner
        self.evaluator = evaluator
        self.context = context
        self.telemetry = telemetry or NullTelemetry()
        self.rng = random.Random(context.seed)

    def initialize(self, initial: AgentVersion) -> None:
        result = self.evaluator.evaluate(initial, self.context)
        self.initialize_with_result(initial, result)

    def initialize_with_result(self, initial: AgentVersion, result: EvaluationResult) -> None:
        """Seed the run from a matching evaluation already present in cache."""
        self.archive.add_initial(initial, result)
        self.telemetry.emit({
            "event": "evaluation_completed",
            "run_id": self.context.run_id,
            "agent_id": initial.version_id,
            "evaluation_id": result.evaluation_id,
            "status": result.status,
        })

    def step(self, iteration: int) -> AgentVersion:
        child_counts = {version.version_id: 0 for version in self.archive.members}
        for candidate in self.archive.history:
            result = self.archive.results[candidate.version_id]
            is_valid = result.score is not None and result.status.upper() not in {"BLOCKED", "INCOMPLETE"}
            if is_valid and candidate.parent_id in child_counts:
                child_counts[candidate.parent_id] += 1
        parent = self.parent_selector.select(
            self.archive.members,
            self.archive.results,
            rng=self.rng,
            child_counts=child_counts,
        )
        child_id = f"{self.context.run_id}-iter-{iteration:04d}"
        self.telemetry.emit({
            "event": "parent_selected",
            "run_id": self.context.run_id,
            "iteration": iteration,
            "parent_id": parent.version_id,
            "selector": type(self.parent_selector).__name__,
        })
        child = self.mutation_runner.mutate(
            parent,
            parent_result=self.archive.results[parent.version_id],
            child_id=child_id,
            context=self.context,
        )
        if child.parent_id != parent.version_id:
            raise ValueError("mutation runner returned a child with the wrong parent_id")
        result = self.evaluator.evaluate(child, self.context)
        self.archive.record(child, result)
        self.telemetry.emit({
            "event": "evaluation_completed",
            "run_id": self.context.run_id,
            "iteration": iteration,
            "agent_id": child.version_id,
            "evaluation_id": result.evaluation_id,
            "status": result.status,
            "score": result.score,
            "archive_members": [item.version_id for item in self.archive.members],
        })
        return child

    def run(self, iterations: int, output_dir: Path) -> None:
        for iteration in range(1, iterations + 1):
            self.step(iteration)
        self.archive.write(output_dir)
