"""Keep the checked-in efficient SWE-bench evaluation selection well-formed."""

import json
from collections import Counter
from pathlib import Path


def test_swebench_verified_100_manifest_is_unique_and_stratified() -> None:
    path = Path(__file__).parents[1] / "benchmarks" / "swebench-verified-100.json"
    manifest = json.loads(path.read_text())

    selected = [
        instance_id
        for repository in manifest["repositories"]
        for instance_id in repository["selected"]
    ]

    assert manifest["source_dataset"] == "SWE-bench/SWE-bench_Verified"
    assert manifest["split"] == "test"
    assert manifest["selection"]["seed"] == 590
    assert manifest["selection"]["size"] == 100
    assert len(selected) == 100
    assert len(set(selected)) == 100
    repository_counts = Counter(instance_id.split("__", 1)[0] for instance_id in selected)
    assert len(manifest["repositories"]) == 12
    assert len(repository_counts) == 12
    assert all(repository["selected"] for repository in manifest["repositories"])
