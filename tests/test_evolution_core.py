import json
import hashlib
from dataclasses import replace
from pathlib import Path
from uuid import uuid4

import pytest

from ecode_core.archive import Archive, KeepLast
from ecode_core.adapters.ecode_evaluator import ECodeEvaluator
from ecode_core.contracts import AgentVersion, ArtifactRef, EvaluationContext, EvaluationResult
from ecode_core.offline_fixture import run_fixture
from ecode_core.selectors import BestScoreParentSelector


def _version(version_id, parent_id=None):
    return AgentVersion(
        version_id=version_id,
        parent_id=parent_id,
        commit_sha=None,
        source_tree_sha256=f"tree-{version_id}",
        config_sha256="config-1",
        artifact=ArtifactRef(f"{version_id}.txt", f"hash-{version_id}", "text/plain"),
    )


def _result(version):
    return EvaluationResult(
        evaluation_id=f"eval-{version.version_id}",
        agent_id=version.version_id,
        score=0.0,
        status="FIXTURE_PASS",
        commit_sha=version.commit_sha,
        source_tree_sha256=version.source_tree_sha256,
        config_sha256=version.config_sha256,
        model="fixture-model",
        provider="none",
        benchmark="fixture",
        segment="fixture-v1",
        artifacts=(version.artifact,),
    )


def test_archive_retention_is_independent_of_score():
    archive = Archive(KeepLast(1))
    first = _version("first")
    second = _version("second", "first")
    archive.add_initial(first, _result(first))
    archive.record(second, _result(second))

    assert [version.version_id for version in archive.history] == ["first", "second"]
    assert [version.version_id for version in archive.members] == ["second"]
    assert archive.results["first"].score == archive.results["second"].score


def test_best_score_selector_is_only_a_parent_selection_policy():
    first = _version("first")
    second = _version("second", "first")
    results = {
        "first": _result(first),
        "second": replace(_result(second), score=2.0),
    }

    selected = BestScoreParentSelector().select(
        (first, second),
        results,
        rng=None,
    )

    assert selected.version_id == "second"


def test_evaluation_result_requires_reproducibility_fields():
    with pytest.raises(ValueError, match="provider"):
        EvaluationResult(
            evaluation_id="e1",
            agent_id="a1",
            score=1.0,
            status="COMPLETE",
            commit_sha=None,
            source_tree_sha256="tree",
            config_sha256="config",
            model="fixture",
            provider="",
            benchmark="fixture",
            segment="v1",
            artifacts=(),
        )


def test_legacy_ecode_evaluator_adapter_carries_provenance_and_artifact_hash():
    tmp_path = Path(".provenance") / f"pytest-adapter-{uuid4().hex}"
    tmp_path.mkdir(parents=True)
    version = _version("legacy-candidate")
    evaluation_file = tmp_path / "swe-result.json"
    evaluation_file.write_text('{"resolved": 1}\n', encoding="utf-8")
    context = EvaluationContext(
        run_id="legacy-run",
        commit_sha=None,
        config_sha256="config-1",
        model="fixture-model",
        provider="local-openai-compatible",
        benchmark="SWE-bench",
        segment="verified-small",
        artifact_dir=tmp_path,
        seed=11,
    )
    adapter = ECodeEvaluator(
        lambda agent, ctx: {
            "evaluation_id": "legacy-eval-1",
            "status": "COMPLETED",
            "overall_performance": {
                "accuracy_score": 1.0,
                "files": [evaluation_file.name],
            },
        }
    )

    result = adapter.evaluate(version, context)

    assert result.commit_sha is None
    assert result.config_sha256 == "config-1"
    assert result.model == "fixture-model"
    assert result.provider == "local-openai-compatible"
    assert (result.benchmark, result.segment) == ("SWE-bench", "verified-small")
    assert len(result.artifacts) == 1
    assert result.artifacts[0].sha256 == hashlib.sha256(evaluation_file.read_bytes()).hexdigest()


def test_offline_fixture_writes_provenance_lineage_and_checksums():
    output_root = Path(".provenance") / f"pytest-evolution-{uuid4().hex}"
    run_dir = run_fixture(output_root, seed=17, iterations=3)
    config = json.loads((run_dir / "run_config.json").read_text(encoding="utf-8"))
    archive = json.loads((run_dir / "archive.json").read_text(encoding="utf-8"))
    lineage = json.loads((run_dir / "lineage.json").read_text(encoding="utf-8"))
    checksums = (run_dir / "checksums.sha256").read_text(encoding="utf-8").splitlines()

    assert config["provider_calls"] is False
    assert config["repository_commit_sha"] is None
    assert len(archive["history"]) == 4
    assert len(lineage) == 4
    assert [item["parent_id"] for item in lineage[1:]]
    assert all(
        result["config_sha256"] == next(
            version["config_sha256"]
            for version in archive["history"]
            if version["version_id"] == result["agent_id"]
        )
        for result in archive["evaluations"].values()
    )
    assert len(checksums) >= 10
    for line in checksums:
        digest, relative_path = line.split("  ", 1)
        assert len(digest) == 64
        assert hashlib.sha256((run_dir / relative_path).read_bytes()).hexdigest() == digest
