import hashlib
import json

import pytest

import swe_bench.harness as harness


def _write_snapshot(root, *, revision=None, parquet_bytes=b"parquet", sha256=None):
    root.mkdir()
    parquet = root / "test.parquet"
    parquet.write_bytes(parquet_bytes)
    actual_sha256 = hashlib.sha256(parquet_bytes).hexdigest()
    manifest = {
        "dataset": "princeton-nlp/SWE-bench_Verified",
        "split": "test",
        "revision": revision or harness.SWE_BENCH_VERIFIED_REVISION,
        "sha256": sha256 or actual_sha256,
    }
    (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return parquet


def test_validate_snapshot_accepts_matching_revision_and_hash(tmp_path):
    root = tmp_path / "snapshot"
    parquet = _write_snapshot(root)

    assert harness._validate_swebench_verified_snapshot(root) == parquet


@pytest.mark.parametrize("missing_name", ["test.parquet", "manifest.json"])
def test_validate_snapshot_fails_closed_when_required_file_is_missing(tmp_path, missing_name):
    root = tmp_path / "snapshot"
    _write_snapshot(root)
    (root / missing_name).unlink()

    with pytest.raises(FileNotFoundError):
        harness._validate_swebench_verified_snapshot(root)


def test_validate_snapshot_rejects_wrong_revision(tmp_path):
    root = tmp_path / "snapshot"
    _write_snapshot(root, revision="wrong")

    with pytest.raises(RuntimeError, match="frozen revision"):
        harness._validate_swebench_verified_snapshot(root)


def test_validate_snapshot_rejects_hash_mismatch(tmp_path):
    root = tmp_path / "snapshot"
    _write_snapshot(root, sha256="0" * 64)

    with pytest.raises(RuntimeError, match="SHA-256"):
        harness._validate_swebench_verified_snapshot(root)


def test_load_snapshot_uses_local_parquet_and_validates_cardinality(tmp_path):
    root = tmp_path / "snapshot"
    parquet = _write_snapshot(root)
    rows = [{"instance_id": f"task-{i}"} for i in range(harness.SWE_BENCH_VERIFIED_ROWS)]
    calls = []

    def fake_load_dataset(name, *, data_files, split):
        calls.append((name, data_files, split))
        return rows

    result = harness._load_swebench_verified_snapshot(
        root,
        dataset_loader=fake_load_dataset,
    )
    assert result == rows
    assert calls == [("parquet", {"test": str(parquet)}, "test")]


def test_load_snapshot_rejects_duplicate_instance_ids(tmp_path):
    root = tmp_path / "snapshot"
    _write_snapshot(root)
    rows = [{"instance_id": "duplicate"} for _ in range(harness.SWE_BENCH_VERIFIED_ROWS)]

    with pytest.raises(RuntimeError, match="not unique"):
        harness._load_swebench_verified_snapshot(
            root,
            dataset_loader=lambda *args, **kwargs: rows,
        )
