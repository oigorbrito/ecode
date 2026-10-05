import json
import hashlib
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from uuid import uuid4

import pytest

from ecode_core.archive import Archive, KeepLast
from ecode_core.adapters.ecode_evaluator import ECodeEvaluator
from ecode_core.adapters.ecode_mutation import ECodeMutationRunner
from ecode_core.contracts import AgentVersion, ArtifactRef, EvaluationContext, EvaluationResult
from ecode_core.offline_fixture import _repository_provenance, run_fixture
from ecode_core.legacy_evaluation import run_benchmark_evaluation
from ecode_core.selectors import BestScoreParentSelector, DGMWeightedParentSelector
from ecode import choose_selfimproves


def _version(version_id, parent_id=None):
    return AgentVersion(
        version_id=version_id,
        parent_id=parent_id,
        commit_sha=None,
        candidate_sha256=f"tree-{version_id}",
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
        candidate_sha256=version.candidate_sha256,
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


@pytest.mark.parametrize("status", ["BLOCKED", "INCOMPLETE", "blocked"])
def test_archive_keeps_unusable_results_in_lineage_but_not_parent_pool(status):
    archive = Archive(KeepLast(5))
    parent = _version("parent")
    blocked = _version("blocked-child", "parent")
    archive.add_initial(parent, _result(parent))
    archive.record(blocked, replace(_result(blocked), status=status, score=999.0))

    assert [version.version_id for version in archive.history] == ["parent", "blocked-child"]
    assert [version.version_id for version in archive.members] == ["parent"]
    assert "blocked-child" in archive.results


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


def test_dgm_weighted_parent_selector_applies_score_and_child_penalty():
    parent = _version("parent")
    child = _version("child", "parent")
    other = _version("other")
    versions = (parent, child, other)
    results = {
        "parent": replace(_result(parent), score=0.8),
        "child": replace(_result(child), score=0.8),
        "other": replace(_result(other), score=0.2),
    }

    class RecordingRng:
        def __init__(self):
            self.arguments = None

        def choices(self, population, *, weights, k):
            self.arguments = (tuple(item.version_id for item in population), tuple(weights), k)
            return [population[1]]

    rng = RecordingRng()
    selected = DGMWeightedParentSelector().select(versions, results, rng=rng)

    assert selected.version_id == "child"
    ids, weights, k = rng.arguments
    assert ids == ("parent", "child", "other")
    assert weights[1] == pytest.approx(weights[0] * 2)
    assert weights[2] < weights[0]
    assert k == 1


def test_dgm_weighted_parent_selector_rejects_invalid_parameters():
    with pytest.raises(ValueError, match="lambda"):
        DGMWeightedParentSelector(lam=float("inf"))


def test_evaluation_result_requires_reproducibility_fields():
    with pytest.raises(ValueError, match="provider"):
        EvaluationResult(
            evaluation_id="e1",
            agent_id="a1",
            score=1.0,
            status="COMPLETE",
            commit_sha=None,
            candidate_sha256="tree",
            config_sha256="config",
            model="fixture",
            provider="",
            benchmark="fixture",
            segment="v1",
            artifacts=(),
        )


def test_ecode_mutation_runner_returns_hashed_patch_artifact_without_evaluation():
    output_dir = Path(".provenance") / f"pytest-mutation-adapter-{uuid4().hex}"
    output_dir.mkdir(parents=True)
    patch_file = output_dir / "candidate.diff"
    patch_file.write_text("diff --git a/file b/file\n", encoding="utf-8")
    parent = _version("parent")
    context = EvaluationContext(
        run_id="mutation-run",
        commit_sha="base-commit",
        config_sha256="config-1",
        model="fixture-model",
        provider="offline-fixture",
        benchmark="fixture",
        segment="fixture-v1",
        artifact_dir=output_dir.resolve(),
        seed=5,
    )
    calls = []

    parent_result = _result(parent)

    def mutate_fn(agent, result, child_id, entry, ctx):
        assert result is parent_result
        calls.append((agent.version_id, child_id, entry, ctx.run_id))
        return {"status": "MUTATION_READY", "model_patch_file": str(patch_file)}

    runner = ECodeMutationRunner(
        mutate_fn=mutate_fn,
        entry_selector=lambda agent, result, ctx: "fixture-task",
    )
    child = runner.mutate(
        parent,
        parent_result=parent_result,
        child_id="child-1",
        context=context,
    )

    expected_hash = hashlib.sha256(patch_file.read_bytes()).hexdigest()
    assert calls == [("parent", "child-1", "fixture-task", "mutation-run")]
    assert child.version_id == "child-1"
    assert child.parent_id == "parent"
    assert child.commit_sha == "base-commit"
    assert child.candidate_sha256 == expected_hash
    assert child.artifact.sha256 == expected_hash
    assert child.attributes["mutation"]["status"] == "MUTATION_READY"


def test_engine_can_seed_from_cached_result_without_running_evaluator():
    from ecode_core.engine import EvolutionEngine
    from ecode_core.telemetry import NullTelemetry

    class NeverEvaluate:
        def evaluate(self, agent, context):
            raise AssertionError("cached initial evaluation must not be repeated")

    class UnusedMutation:
        def mutate(self, parent, *, parent_result, child_id, context):
            raise AssertionError("initialization should not mutate")

    output_dir = Path(".provenance") / f"pytest-cached-seed-{uuid4().hex}"
    initial = _version("cached-initial")
    cached_result = _result(initial)
    context = EvaluationContext(
        run_id="cached-run",
        commit_sha=None,
        config_sha256="config-1",
        model="fixture-model",
        provider="offline-fixture",
        benchmark="fixture",
        segment="cached-baseline-v1",
        artifact_dir=output_dir,
        seed=19,
    )
    engine = EvolutionEngine(
        archive=Archive(KeepLast(2)),
        parent_selector=BestScoreParentSelector(),
        mutation_runner=UnusedMutation(),
        evaluator=NeverEvaluate(),
        context=context,
        telemetry=NullTelemetry(),
    )

    engine.initialize_with_result(initial, cached_result)

    assert engine.archive.history == [initial]
    assert engine.archive.results[initial.version_id] is cached_result


def test_legacy_ecode_evaluator_adapter_carries_provenance_and_artifact_hash():
    tmp_path = Path(".provenance") / f"pytest-adapter-{uuid4().hex}"
    tmp_path.mkdir(parents=True)
    version = _version("legacy-candidate")
    candidate_file = tmp_path / "agent.patch"
    candidate_file.write_text("candidate patch", encoding="utf-8")
    version = replace(
        version,
        artifact=ArtifactRef(
            str(candidate_file.resolve()),
            hashlib.sha256(candidate_file.read_bytes()).hexdigest(),
            "text/x-diff",
        ),
    )
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
        artifact_dir=tmp_path.resolve(),
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
    assert len(result.artifacts) == 2
    assert result.artifacts[0].path == version.artifact.path
    assert result.artifacts[0].sha256 == version.artifact.sha256
    assert result.artifacts[1].sha256 == hashlib.sha256(evaluation_file.read_bytes()).hexdigest()


def test_ecode_evaluator_can_convert_cached_metadata_without_running_harness():
    output_dir = (Path(".provenance") / f"pytest-cached-metadata-{uuid4().hex}").resolve()
    output_dir.mkdir(parents=True)
    agent_file = output_dir / "agent.txt"
    agent_file.write_text("agent artifact", encoding="utf-8")
    agent = AgentVersion(
        version_id="cached-agent",
        parent_id=None,
        commit_sha=None,
        candidate_sha256=hashlib.sha256(agent_file.read_bytes()).hexdigest(),
        config_sha256="cached-config",
        artifact=ArtifactRef(
            str(agent_file),
            hashlib.sha256(agent_file.read_bytes()).hexdigest(),
            "text/plain",
        ),
    )
    context = EvaluationContext(
        run_id="cached-run",
        commit_sha=None,
        config_sha256="cached-config",
        model="cached-model",
        provider="cached-provider",
        benchmark="SWE-bench",
        segment="verified-small",
        artifact_dir=output_dir,
        seed=7,
    )

    result = ECodeEvaluator.from_metadata(
        agent,
        context,
        {
            "evaluation_id": "cached-evaluation",
            "status": "COMPLETED",
            "overall_performance": {"accuracy_score": 0.75},
        },
    )

    assert result.evaluation_id == "cached-evaluation"
    assert result.score == 0.75
    assert result.provider == "cached-provider"
    assert result.benchmark == "SWE-bench"
    assert result.segment == "verified-small"


def test_ecode_evaluator_does_not_turn_blocked_score_into_evidence():
    artifact_dir = (Path(".provenance") / f"pytest-blocked-evaluator-{uuid4().hex}").resolve()
    artifact_dir.mkdir(parents=True)
    agent_path = artifact_dir / "agent.patch"
    agent_path.write_text("patch", encoding="utf-8")
    agent_hash = hashlib.sha256(agent_path.read_bytes()).hexdigest()
    version = AgentVersion(
        version_id="blocked-agent",
        parent_id=None,
        commit_sha=None,
        candidate_sha256=agent_hash,
        config_sha256="config-1",
        artifact=ArtifactRef(str(agent_path.resolve()), agent_hash, "text/x-diff"),
    )
    context = EvaluationContext(
        run_id="blocked-run",
        commit_sha=None,
        config_sha256="config-1",
        model="fixture-model",
        provider="none",
        benchmark="fixture",
        segment="fixture-v1",
        artifact_dir=artifact_dir,
        seed=3,
    )

    result = ECodeEvaluator(lambda agent, ctx: {
        "status": "BLOCKED",
        "blocked_reason": "SANDBOX_UNAVAILABLE",
        "overall_performance": {"accuracy_score": 1.0},
    }).evaluate(version, context)

    assert result.status == "BLOCKED"
    assert result.score is None
    assert result.metadata["blocked_reason"] == "SANDBOX_UNAVAILABLE"
    assert result.artifacts == (version.artifact,)


def test_offline_fixture_writes_provenance_lineage_and_checksums():
    output_root = Path(".provenance") / f"pytest-evolution-{uuid4().hex}"
    run_dir = run_fixture(output_root, seed=17, iterations=3)
    config = json.loads((run_dir / "run_config.json").read_text(encoding="utf-8"))
    archive = json.loads((run_dir / "archive.json").read_text(encoding="utf-8"))
    lineage = json.loads((run_dir / "lineage.json").read_text(encoding="utf-8"))
    baseline = json.loads((run_dir / "baseline_manifest.json").read_text(encoding="utf-8"))
    checksums = (run_dir / "checksums.sha256").read_text(encoding="utf-8").splitlines()
    repository = _repository_provenance()

    assert config["provider_calls"] is False
    assert config["baseline_origin"] == "NEW_LOCAL_BASELINE"
    assert config["repository_head_sha"] == repository["head_sha"]
    assert config["repository_worktree_dirty"] == repository["worktree_dirty"]
    assert config["repository_commit_sha"] == repository["commit_sha"]
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
    assert baseline["baseline_origin"] == "NEW_LOCAL_BASELINE"
    assert baseline["baseline_scope"] == "provider-free-integration-fixture"
    assert baseline["seed"] == 17
    assert baseline["dataset"]["source"] == "synthetic deterministic fixture; no external dataset"
    assert baseline["environment"]["python_version"]
    assert baseline["environment"]["installed_distributions"]
    assert baseline["environment"]["installed_distributions_sha256"] == hashlib.sha256(
        "\n".join(baseline["environment"]["installed_distributions"]).encode("utf-8")
    ).hexdigest()
    assert baseline["dataset_sha256"] == hashlib.sha256(
        (run_dir / baseline["dataset_artifact"]).read_bytes()
    ).hexdigest()
    assert baseline["config_sha256"] == hashlib.sha256(
        (run_dir / "run_config.json").read_bytes()
    ).hexdigest()
    assert baseline["environment_artifact"] == "artifacts/provenance/environment.json"
    assert "artifacts/provenance/source_snapshot/ecode.py" in {
        artifact["path"] for artifact in baseline["artifacts"]
    }
    source_digest = hashlib.sha256()
    source_root = run_dir / "artifacts/provenance/source_snapshot"
    for relative in sorted(baseline["code_files"]):
        encoded_path = relative.encode("utf-8")
        content = (source_root / relative).read_bytes()
        source_digest.update(len(encoded_path).to_bytes(8, "big"))
        source_digest.update(encoded_path)
        source_digest.update(len(content).to_bytes(8, "big"))
        source_digest.update(content)
    assert baseline["code_sha256"] == source_digest.hexdigest()
    for name, digest in baseline["dependency_manifests_sha256"].items():
        dependency_path = run_dir / "artifacts/provenance/dependency_manifests" / name
        assert hashlib.sha256(dependency_path.read_bytes()).hexdigest() == digest
    assert baseline["qualification"]["real_model_capability"] == "NOT_EXECUTED"
    assert baseline["qualification"]["performance_gain"] == "NOT_PROVEN"
    for artifact in baseline["artifacts"]:
        assert hashlib.sha256((run_dir / artifact["path"]).read_bytes()).hexdigest() == artifact["sha256"]
    for line in checksums:
        digest, relative_path = line.split("  ", 1)
        assert len(digest) == 64
        assert hashlib.sha256((run_dir / relative_path).read_bytes()).hexdigest() == digest


def test_repository_provenance_is_unknown_when_git_is_unavailable(monkeypatch):
    def git_unavailable(*args, **kwargs):
        raise FileNotFoundError("git executable unavailable")

    monkeypatch.setattr("ecode_core.offline_fixture.subprocess.run", git_unavailable)
    assert _repository_provenance() == {
        "head_sha": None,
        "commit_sha": None,
        "worktree_dirty": None,
    }


def test_legacy_best_selection_chooses_highest_scoring_candidate(monkeypatch):
    output_dir = Path(".provenance") / f"pytest-legacy-selector-{uuid4().hex}"
    monkeypatch.setattr("ecode.random.random", lambda: 1.0)
    monkeypatch.setattr("ecode.any_exceeding_context_length", lambda *args: False)
    for version_id, score, parent_id in (
        ("initial", 0.1, None),
        ("child", 0.9, "initial"),
    ):
        version_dir = output_dir / version_id
        version_dir.mkdir(parents=True)
        metadata = {
            "parent_commit": parent_id,
            "overall_performance": {
                "accuracy_score": score,
                "total_unresolved_ids": [f"task-{version_id}"],
                "total_emptypatch_ids": [],
                "total_resolved_ids": [],
            },
        }
        (version_dir / "metadata.json").write_text(
            json.dumps(metadata),
            encoding="utf-8",
        )

    selected = choose_selfimproves(
        str(output_dir),
        ["initial", "child"],
        1,
        method="best",
    )
    engine_versions = (_version("initial"), _version("child", "initial"))
    engine_results = {
        "initial": replace(_result(engine_versions[0]), score=0.1),
        "child": replace(_result(engine_versions[1]), score=0.9),
    }
    engine_selected = BestScoreParentSelector().select(
        engine_versions,
        engine_results,
        rng=None,
    )

    assert selected == [("child", "task-child")]
    assert engine_selected.version_id == selected[0][0]


def test_ecode_cli_exposes_provider_free_core_fixture():
    output_dir = Path(".provenance") / f"pytest-cli-fixture-{uuid4().hex}"
    repository_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [
            sys.executable,
            "ecode.py",
            "--offline-fixture",
            "--fixture-output-dir",
            str(output_dir),
            "--fixture-seed",
            "13",
            "--fixture-iterations",
            "2",
        ],
        cwd=repository_root,
        capture_output=True,
        text=True,
        check=True,
    )
    run_dir = output_dir / "offline-fixture-seed-13-parent-random-retention-keep-all"
    config = json.loads((run_dir / "run_config.json").read_text(encoding="utf-8"))

    assert "Offline fixture evidence:" in result.stdout
    assert config["provider_calls"] is False
    assert config["iterations"] == 2


def test_ecode_cli_dgm_engine_is_opt_in_fixture_with_dgm_selection():
    output_dir = Path(".provenance") / f"pytest-cli-dgm-{uuid4().hex}"
    repository_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [
            sys.executable,
            "ecode.py",
            "--engine",
            "dgm",
            "--fixture-parent-selector",
            "dgm-weighted",
            "--fixture-output-dir",
            str(output_dir),
            "--fixture-seed",
            "19",
            "--fixture-iterations",
            "2",
        ],
        cwd=repository_root,
        capture_output=True,
        text=True,
        check=True,
    )
    run_dir = output_dir / "offline-fixture-seed-19-parent-dgm-weighted-retention-keep-all"
    config = json.loads((run_dir / "run_config.json").read_text(encoding="utf-8"))
    archive = json.loads((run_dir / "archive.json").read_text(encoding="utf-8"))
    lineage = json.loads((run_dir / "lineage.json").read_text(encoding="utf-8"))
    baseline = json.loads((run_dir / "baseline_manifest.json").read_text(encoding="utf-8"))

    assert "DGM fixture evidence:" in result.stdout
    assert config["execution_mode"] == "dgm-fixture"
    assert baseline["baseline_id"].startswith("ECODE-DGM-FIXTURE-")
    assert baseline["baseline_origin"] == "NEW_LOCAL_BASELINE"
    assert config["parent_selector"] == "dgm-weighted"
    assert config["provider_calls"] is False
    assert len(archive["history"]) == 3
    assert len(lineage) == 3
    assert [item["parent_id"] for item in lineage[1:]]


def test_ecode_cli_rejects_production_options_for_dgm_engine():
    output_dir = Path(".provenance") / f"pytest-cli-dgm-reject-{uuid4().hex}"
    repository_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [
            sys.executable,
            "ecode.py",
            "--engine",
            "dgm",
            "--max_generation",
            "2",
            "--fixture-output-dir",
            str(output_dir),
        ],
        cwd=repository_root,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "--engine dgm is fixture-only" in result.stderr
    assert not output_dir.exists()


@pytest.mark.parametrize("args", [[], ["--engine", "legacy"]])
def test_ecode_cli_uses_legacy_production_dispatch_by_default_or_explicitly(monkeypatch, args):
    import ecode
    from types import ModuleType

    class LegacyDispatchReached(Exception):
        pass

    def stop_at_legacy_initialization(*args, **kwargs):
        raise LegacyDispatchReached

    monkeypatch.setattr(ecode, "initialize_run", stop_at_legacy_initialization)
    monkeypatch.setattr(ecode.os, "makedirs", lambda *args, **kwargs: None)
    mutation_module = ModuleType("self_improve_step")
    mutation_module.self_improve = lambda *args, **kwargs: None
    common_module = ModuleType("utils.common_utils")
    common_module.load_json_file = lambda *args, **kwargs: []
    docker_module = ModuleType("utils.docker_utils")
    docker_module.setup_logger = lambda *args, **kwargs: None
    evo_module = ModuleType("utils.evo_utils")
    evo_module.load_ecode_metadata = lambda *args, **kwargs: None
    evo_module.is_compiled_self_improve = lambda *args, **kwargs: False
    for name, module in (
        ("self_improve_step", mutation_module),
        ("utils.common_utils", common_module),
        ("utils.docker_utils", docker_module),
        ("utils.evo_utils", evo_module),
    ):
        monkeypatch.setitem(sys.modules, name, module)

    with pytest.raises(LegacyDispatchReached):
        ecode.main(args)


def test_evaluation_phase_consumes_existing_mutation_without_regenerating_it():
    output_dir = Path(".provenance") / f"pytest-evaluation-phase-{uuid4().hex}"
    output_dir.mkdir(parents=True)
    patch_file = output_dir / "model_patch.diff"
    patch_file.write_text("diff --git a/x b/x\n", encoding="utf-8")
    calls = []

    def fake_harness(entry, model, patches, num_evals, out, metadata, run_id, threshold, tasks, more):
        calls.append((entry, model, tuple(patches), num_evals, run_id))
        metadata["overall_performance"] = {"accuracy_score": 0.25}

    metadata = {"run_id": "candidate-1"}
    result = run_benchmark_evaluation(
        model_patch_file=str(patch_file),
        metadata=metadata,
        harness_runner=fake_harness,
        sandbox_unavailable_error=RuntimeError,
        harness_args=("fixture-task", "candidate-1", [str(patch_file)], 1, str(output_dir), metadata, "candidate-1", None, ["fixture-task"], None),
        log=lambda message: None,
        persist=lambda value: (output_dir / "metadata.json").write_text(json.dumps(value), encoding="utf-8"),
    )

    assert calls == [("fixture-task", "candidate-1", (str(patch_file),), 1, "candidate-1")]
    assert result["model_patch_notempty"] is True
    assert result["overall_performance"]["accuracy_score"] == 0.25
    assert not (output_dir / "metadata.json").exists()


def test_evaluation_phase_keeps_sandbox_unavailable_blocked():
    class SandboxUnavailableError(RuntimeError):
        pass

    output_dir = Path(".provenance") / f"pytest-evaluation-blocked-{uuid4().hex}"
    output_dir.mkdir(parents=True)
    patch_file = output_dir / "model_patch.diff"
    patch_file.write_text("patch\n", encoding="utf-8")

    def unavailable(*args, **kwargs):
        raise SandboxUnavailableError("sandbox unavailable")

    persisted = []
    result = run_benchmark_evaluation(
        model_patch_file=str(patch_file),
        metadata={"run_id": "candidate-blocked"},
        harness_runner=unavailable,
        sandbox_unavailable_error=RuntimeError,
        harness_args=(),
        log=lambda message: None,
        persist=lambda value: persisted.append(dict(value)),
    )

    assert result["status"] == "BLOCKED"
    assert result["blocked_reason"] == "SANDBOX_UNAVAILABLE"
    assert persisted == [result]
