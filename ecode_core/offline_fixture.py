from __future__ import annotations

import argparse
import hashlib
from importlib.metadata import distributions
import json
import platform
import subprocess
import sys
from pathlib import Path

from .archive import Archive, KeepAll, KeepLast
from .contracts import AgentVersion, ArtifactRef, EvaluationContext, EvaluationResult
from .engine import EvolutionEngine
from .selectors import BestScoreParentSelector, DGMWeightedParentSelector, RandomParentSelector
from .telemetry import JsonlTelemetry


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _source_digest(repository_root: Path, files: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(files):
        relative = path.relative_to(repository_root).as_posix().encode("utf-8")
        content = path.read_bytes()
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def _repository_provenance(repository_root: Path | None = None) -> dict[str, object]:
    """Return a commit identity only when it describes the current source tree."""
    root = repository_root or Path(__file__).resolve().parent.parent
    try:
        head_sha = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        status = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return {"head_sha": None, "commit_sha": None, "worktree_dirty": None}

    dirty = bool(status.strip())
    return {
        "head_sha": head_sha or None,
        "commit_sha": None if dirty else (head_sha or None),
        "worktree_dirty": dirty,
    }


class FixtureMutationRunner:
    """Deterministic mutation simulation; makes no model or provider calls."""

    def mutate(self, parent, *, parent_result, child_id, context):
        parent_text = Path(parent.artifact.path).read_text(encoding="utf-8")
        next_quality = int(parent.attributes["fixture_quality"]) + 1
        content = f"{parent_text}\nfixture_mutation={child_id}\nquality={next_quality}\n"
        artifact_path = context.artifact_dir / "agents" / f"{child_id}.txt"
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text(content, encoding="utf-8")
        data = content.encode("utf-8")
        digest = _sha256(data)
        return AgentVersion(
            version_id=child_id,
            parent_id=parent.version_id,
            commit_sha=context.commit_sha,
            candidate_sha256=digest,
            config_sha256=context.config_sha256,
            artifact=ArtifactRef(str(artifact_path), digest, "text/plain"),
            attributes={"fixture_quality": next_quality},
        )


class FixtureEvaluator:
    """Deterministic offline evaluator used only to qualify engine plumbing."""

    def evaluate(self, agent, context):
        score = float(agent.attributes["fixture_quality"])
        evaluation_id = f"{context.run_id}:{agent.version_id}"
        evaluation = {
            "evaluation_id": evaluation_id,
            "agent_id": agent.version_id,
            "score": score,
            "status": "FIXTURE_PASS",
            "commit_sha": agent.commit_sha,
            "candidate_sha256": agent.candidate_sha256,
            "config_sha256": context.config_sha256,
            "model": context.model,
            "provider": context.provider,
            "benchmark": context.benchmark,
            "segment": context.segment,
            "agent_artifact": agent.artifact.path,
            "agent_artifact_sha256": agent.artifact.sha256,
        }
        artifact_path = context.artifact_dir / "evaluations" / f"{agent.version_id}.json"
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        data = (json.dumps(evaluation, indent=2, sort_keys=True) + "\n").encode("utf-8")
        artifact_path.write_bytes(data)
        return EvaluationResult(
            evaluation_id=evaluation_id,
            agent_id=agent.version_id,
            score=score,
            status="FIXTURE_PASS",
            commit_sha=agent.commit_sha,
            candidate_sha256=agent.candidate_sha256,
            config_sha256=context.config_sha256,
            model=context.model,
            provider=context.provider,
            benchmark=context.benchmark,
            segment=context.segment,
            artifacts=(
                agent.artifact,
                ArtifactRef(str(artifact_path), _sha256(data), "application/json"),
            ),
            evaluated_at="2000-01-01T00:00:00+00:00",
            metadata={"evaluation_kind": "offline_fixture"},
        )


def run_fixture(
    output_dir: Path,
    *,
    seed: int = 7,
    iterations: int = 3,
    parent_selector: str = "random",
    retention: str = "keep-all",
    archive_limit: int = 3,
    execution_mode: str = "offline-fixture",
) -> Path:
    if iterations < 1:
        raise ValueError("iterations must be at least one")
    if parent_selector not in {"random", "best-score", "dgm-weighted"}:
        raise ValueError("parent_selector must be random, best-score, or dgm-weighted")
    if retention not in {"keep-all", "keep-last"}:
        raise ValueError("retention must be keep-all or keep-last")
    if archive_limit < 1:
        raise ValueError("archive_limit must be at least one")
    if execution_mode not in {"offline-fixture", "dgm-fixture"}:
        raise ValueError("execution_mode must be offline-fixture or dgm-fixture")
    run_id = f"offline-fixture-seed-{seed}-parent-{parent_selector}-retention-{retention}"
    run_dir = output_dir / run_id
    if run_dir.exists():
        raise FileExistsError(f"Refusing to overwrite existing evidence bundle: {run_dir}")
    run_dir.mkdir(parents=True)

    repository_root = Path(__file__).resolve().parent.parent
    source_root = repository_root / "ecode_core"
    source_files = sorted(source_root.rglob("*.py"))
    engine_source_hash = hashlib.sha256()
    for source_file in source_files:
        engine_source_hash.update(source_file.relative_to(source_root).as_posix().encode())
        engine_source_hash.update(source_file.read_bytes())
    code_files = [repository_root / "ecode.py", *source_files]
    dependency_paths = [
        path
        for path in (
            repository_root / "pyproject.toml",
            repository_root / "requirements.txt",
            repository_root / "requirements_dev.txt",
        )
        if path.is_file()
    ]
    dependency_manifests = {path.name: _sha256(path.read_bytes()) for path in dependency_paths}
    dataset = {
        "name": "ECodeCoreFixture",
        "source": "synthetic deterministic fixture; no external dataset",
        "specification": "ECodeCoreFixture/deterministic-v1",
    }
    dataset_bytes = (json.dumps(dataset, indent=2, sort_keys=True) + "\n").encode("utf-8")
    dataset_digest = _sha256(dataset_bytes)
    installed_distributions = sorted(
        f"{distribution.metadata['Name']}=={distribution.version}"
        for distribution in distributions()
        if distribution.metadata.get("Name")
    )
    environment = {
        "python_version": sys.version,
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "system": platform.system(),
        "installed_distributions": installed_distributions,
        "installed_distributions_sha256": _sha256(
            "\n".join(installed_distributions).encode("utf-8")
        ),
    }
    model = "fixture-model-v1"
    provider = "none-offline-fixture"
    benchmark = "ECodeCoreFixture"
    segment = f"deterministic-{iterations}-step-v1"
    repository = _repository_provenance()
    config = {
        "run_id": run_id,
        "execution_mode": execution_mode,
        "baseline_origin": "NEW_LOCAL_BASELINE",
        "seed": seed,
        "iterations": iterations,
        "archive_limit": archive_limit if retention == "keep-last" else None,
        "repository_head_sha": repository["head_sha"],
        "repository_commit_sha": repository["commit_sha"],
        "repository_worktree_dirty": repository["worktree_dirty"],
        "engine_source_sha256": engine_source_hash.hexdigest(),
        "code_sha256": _source_digest(repository_root, code_files),
        "dependency_manifests_sha256": dependency_manifests,
        "dataset": dataset,
        "dataset_sha256": dataset_digest,
        "environment": environment,
        "parent_selector": parent_selector,
        "archive_retention": retention,
        "mutator": "FixtureMutationRunner",
        "evaluator": "FixtureEvaluator",
        "model": model,
        "provider": provider,
        "benchmark": benchmark,
        "segment": segment,
        "provider_calls": False,
    }
    config_bytes = (json.dumps(config, sort_keys=True) + "\n").encode("utf-8")
    config_sha = _sha256(config_bytes)
    (run_dir / "run_config.json").write_bytes(config_bytes)

    artifact_dir = run_dir / "artifacts"
    context = EvaluationContext(
        run_id=run_id,
        commit_sha=repository["commit_sha"],
        config_sha256=config_sha,
        model=model,
        provider=provider,
        benchmark=benchmark,
        segment=segment,
        artifact_dir=artifact_dir,
        seed=seed,
    )
    initial_bytes = b"fixture_agent=initial\nquality=0\n"
    initial_path = artifact_dir / "agents" / "initial.txt"
    initial_path.parent.mkdir(parents=True, exist_ok=True)
    initial_path.write_bytes(initial_bytes)
    initial_digest = _sha256(initial_bytes)
    initial = AgentVersion(
        version_id="initial",
        parent_id=None,
        commit_sha=repository["commit_sha"],
        candidate_sha256=initial_digest,
        config_sha256=config_sha,
        artifact=ArtifactRef(str(initial_path), initial_digest, "text/plain"),
        attributes={"fixture_quality": 0},
    )

    archive_policy = KeepAll() if retention == "keep-all" else KeepLast(archive_limit)
    selector = {
        "random": RandomParentSelector,
        "best-score": BestScoreParentSelector,
        "dgm-weighted": DGMWeightedParentSelector,
    }[parent_selector]()
    archive = Archive(archive_policy)
    engine = EvolutionEngine(
        archive=archive,
        parent_selector=selector,
        mutation_runner=FixtureMutationRunner(),
        evaluator=FixtureEvaluator(),
        context=context,
        telemetry=JsonlTelemetry(run_dir / "telemetry.jsonl"),
    )
    engine.initialize(initial)
    engine.run(iterations, run_dir)

    provenance_dir = artifact_dir / "provenance"
    source_snapshot_dir = provenance_dir / "source_snapshot"
    for source_file in code_files:
        relative = source_file.relative_to(repository_root)
        snapshot_file = source_snapshot_dir / relative
        snapshot_file.parent.mkdir(parents=True, exist_ok=True)
        snapshot_file.write_bytes(source_file.read_bytes())
    dependency_snapshot_dir = provenance_dir / "dependency_manifests"
    for dependency_file in dependency_paths:
        (dependency_snapshot_dir / dependency_file.name).parent.mkdir(parents=True, exist_ok=True)
        (dependency_snapshot_dir / dependency_file.name).write_bytes(dependency_file.read_bytes())
    dataset_path = provenance_dir / "dataset.json"
    dataset_path.parent.mkdir(parents=True, exist_ok=True)
    dataset_path.write_bytes(dataset_bytes)
    environment_path = provenance_dir / "environment.json"
    environment_path.write_text(
        json.dumps(environment, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    run_artifacts = sorted(path for path in run_dir.rglob("*") if path.is_file())
    baseline_prefix = "ECODE-DGM-FIXTURE" if execution_mode == "dgm-fixture" else "ECODE-CORE-FIXTURE"
    baseline_manifest = {
        "schema_version": 1,
        "baseline_id": f"{baseline_prefix}-{config_sha[:12]}",
        "baseline_origin": "NEW_LOCAL_BASELINE",
        "baseline_scope": "provider-free-integration-fixture",
        "run_id": run_id,
        "execution_mode": execution_mode,
        "code_sha256": config["code_sha256"],
        "code_files": [path.relative_to(repository_root).as_posix() for path in code_files],
        "repository_head_sha": repository["head_sha"],
        "repository_commit_sha": repository["commit_sha"],
        "repository_worktree_dirty": repository["worktree_dirty"],
        "config_sha256": config_sha,
        "dataset": dataset,
        "dataset_artifact": dataset_path.relative_to(run_dir).as_posix(),
        "dataset_sha256": dataset_digest,
        "dependency_manifests_sha256": dependency_manifests,
        "environment_artifact": environment_path.relative_to(run_dir).as_posix(),
        "environment": environment,
        "seed": seed,
        "model": model,
        "provider": provider,
        "benchmark": benchmark,
        "segment": segment,
        "artifacts": [
            {
                "path": path.relative_to(run_dir).as_posix(),
                "sha256": _sha256(path.read_bytes()),
            }
            for path in run_artifacts
        ],
        "qualification": {
            "integration": "PASS",
            "reproducibility": "NOT_ASSESSED_SINGLE_RUN",
            "real_model_capability": "NOT_EXECUTED",
            "performance_gain": "NOT_PROVEN",
            "historical_cache_comparison": "NOT_USABLE_FOR_COMPARISON",
        },
        "attestation": "self-recorded local evidence; hashes identify files but do not authenticate historical origin",
    }
    (run_dir / "baseline_manifest.json").write_text(
        json.dumps(baseline_manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    checksum_lines = []
    for path in sorted(item for item in run_dir.rglob("*") if item.is_file()):
        relative_path = path.relative_to(run_dir).as_posix()
        checksum_lines.append(f"{_sha256(path.read_bytes())}  {relative_path}")
    (run_dir / "checksums.sha256").write_text(
        "\n".join(checksum_lines) + "\n",
        encoding="utf-8",
    )
    return run_dir


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run ECode's offline evolution-core fixture.")
    parser.add_argument("--output-dir", type=Path, default=Path(".provenance/evolution-core"))
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--iterations", type=int, default=3)
    parser.add_argument(
        "--parent-selector",
        choices=("random", "best-score", "dgm-weighted"),
        default="random",
    )
    parser.add_argument("--retention", choices=("keep-all", "keep-last"), default="keep-all")
    parser.add_argument("--archive-limit", type=int, default=3)
    args = parser.parse_args(argv)
    run_dir = run_fixture(
        args.output_dir,
        seed=args.seed,
        iterations=args.iterations,
        parent_selector=args.parent_selector,
        retention=args.retention,
        archive_limit=args.archive_limit,
    )
    print(f"Offline fixture evidence: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
