from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Sequence

from .contracts import AgentVersion, ArchiveRetentionPolicy, EvaluationResult


class KeepAll:
    def retain(self, versions: Sequence[AgentVersion]) -> Sequence[AgentVersion]:
        return tuple(versions)


class KeepLast:
    def __init__(self, limit: int):
        if limit < 1:
            raise ValueError("archive limit must be at least one")
        self.limit = limit

    def retain(self, versions: Sequence[AgentVersion]) -> Sequence[AgentVersion]:
        return tuple(versions[-self.limit :])


class Archive:
    """Candidate history plus configurable parent-selection membership.

    Recording a candidate never promotes it. Retention only determines which
    versions remain available for future parent selection; full history stays
    in the serialized archive and lineage.
    """

    def __init__(self, retention: ArchiveRetentionPolicy):
        self.retention = retention
        self.history: List[AgentVersion] = []
        self.results: Dict[str, EvaluationResult] = {}
        self.members: List[AgentVersion] = []

    def record(self, version: AgentVersion, result: EvaluationResult) -> None:
        if version.version_id in self.results:
            raise ValueError(f"duplicate version id: {version.version_id}")
        if result.agent_id != version.version_id:
            raise ValueError("evaluation result agent_id does not match candidate")
        if result.commit_sha != version.commit_sha:
            raise ValueError("evaluation result commit_sha does not match candidate")
        if result.source_tree_sha256 != version.source_tree_sha256:
            raise ValueError("evaluation result source hash does not match candidate")
        if result.config_sha256 != version.config_sha256:
            raise ValueError("evaluation result config hash does not match candidate")
        self.history.append(version)
        self.results[version.version_id] = result
        self.members = list(self.retention.retain(self.members + [version]))

    def add_initial(self, version: AgentVersion, result: EvaluationResult) -> None:
        if self.history:
            raise ValueError("initial version can only be added to an empty archive")
        self.record(version, result)

    def write(self, output_dir: Path) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)
        lineage = [
            {"version_id": item.version_id, "parent_id": item.parent_id}
            for item in self.history
        ]
        archive_document = {
            "history": [_jsonable(item) for item in self.history],
            "selection_members": [item.version_id for item in self.members],
            "evaluations": {
                version_id: _jsonable(result)
                for version_id, result in self.results.items()
            },
        }
        (output_dir / "archive.json").write_text(
            json.dumps(archive_document, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (output_dir / "lineage.json").write_text(
            json.dumps(lineage, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def _jsonable(value):
    if hasattr(value, "__dataclass_fields__"):
        return {key: _jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    return value
