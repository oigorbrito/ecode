import os
import hashlib
import json
from pathlib import Path
from datasets import load_dataset

SWE_BENCH_VERIFIED_REVISION = "c104f840cc67f8b6eec6f759ebc8b2693d585d4a"
SWE_BENCH_VERIFIED_ROWS = 500

def prepare():
    snapshot_dir = Path(".cache/swebench-verified") / SWE_BENCH_VERIFIED_REVISION
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    
    parquet_path = snapshot_dir / "test.parquet"
    manifest_path = snapshot_dir / "manifest.json"
    
    print("Downloading SWE-bench Verified dataset from Hugging Face...")
    dataset = load_dataset(
        "princeton-nlp/SWE-bench_Verified",
        split="test",
        revision=SWE_BENCH_VERIFIED_REVISION
    )
    
    print(f"Loaded dataset with {len(dataset)} rows.")
    assert len(dataset) == SWE_BENCH_VERIFIED_ROWS, f"Expected {SWE_BENCH_VERIFIED_ROWS} rows, got {len(dataset)}"
    
    # Check uniqueness of instance_id
    instance_ids = [entry["instance_id"] for entry in dataset]
    assert len(set(instance_ids)) == SWE_BENCH_VERIFIED_ROWS, "instance_id values are not unique!"
    
    print(f"Saving dataset as local parquet at {parquet_path}...")
    dataset.to_parquet(str(parquet_path))
    
    # Calculate SHA-256
    parquet_bytes = parquet_path.read_bytes()
    sha256 = hashlib.sha256(parquet_bytes).hexdigest()
    
    manifest = {
        "dataset": "princeton-nlp/SWE-bench_Verified",
        "split": "test",
        "revision": SWE_BENCH_VERIFIED_REVISION,
        "sha256": sha256,
    }
    
    print(f"Writing manifest.json with SHA-256: {sha256}...")
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("Successfully prepared SWE-bench Verified snapshot!")

if __name__ == "__main__":
    prepare()
