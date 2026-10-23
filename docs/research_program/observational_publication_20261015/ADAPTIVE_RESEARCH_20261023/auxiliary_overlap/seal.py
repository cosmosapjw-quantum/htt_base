"""Seal the reviewed-ready R25 candidate without self-referential manifest hashes."""
from __future__ import annotations

import json

from compute import HERE, SOURCE_HASHES, TASK, PACKET, AGENT, sha, dump


def main():
    result = json.loads((HERE/"RESULT.json").read_text())
    assert result["task_id"] == TASK and result["packet_id"] == PACKET
    assert "2 passed" in (HERE/"TEST_STDOUT.txt").read_text()
    for path, expected in SOURCE_HASHES.items():
        assert sha(path) == expected
    products = ["compute.py", "finish.py", "seal.py", "test_compute.py",
                "RESULT.json", "joint_tensor_atomic.npz", "figure.png", "REPORT.md"]
    manifest = {
        "schema": "htt.r25_candidate_manifest/1", "task_id": TASK,
        "packet_id": PACKET,
        "input_identity": "sha256:"+SOURCE_HASHES[next(p for p in SOURCE_HASHES if p.name.endswith("INPUT.json"))],
        "source_base_head": "10f3ea585c6608e794900efe7e4f8f42c0747a3b",
        "source_hashes": {str(p): h for p, h in SOURCE_HASHES.items()},
        "products": {name: {"sha256": sha(HERE/name), "bytes": (HERE/name).stat().st_size}
                     for name in products},
        "excludes_self_and_mutable_receipts": ["MANIFEST.json", "RAW_RECEIPT.json", "RETURN.json"],
    }
    dump(HERE/"MANIFEST.json", manifest)
    candidate = "sha256:"+sha(HERE/"MANIFEST.json")
    receipt = {
        "task_id": TASK, "packet_id": PACKET,
        "input_identity": manifest["input_identity"], "agent_id": AGENT,
        "candidate_identity": candidate,
        "outcome": "success_candidate_pending_independent_review",
        "observed_runtime": "UNKNOWN",
        "requested_runtime": "gpt-6-sol/high",
        "numerical_commands": [
            {"argv": "timeout 75s .venv/bin/python auxiliary_overlap/compute.py",
             "exit": 1, "elapsed_seconds": 4.25,
             "first_failure": str(HERE/"FIRST_FAILURE.txt"),
             "meaning": "all exact, LP and tensor checks completed; presentation import failed under virtual-address ulimit"},
            {"argv": "timeout 20s .venv/bin/python auxiliary_overlap/finish.py",
             "exit": 0, "elapsed_seconds": 19.76,
             "meaning": "presentation from saved numerical output; no further LP"},
            {"argv": "timeout 20s .venv/bin/python -m pytest -q auxiliary_overlap/test_compute.py",
             "exit": 0, "elapsed_seconds": 7.67, "summary": "2 passed"},
            {"argv": "timeout 20s .venv/bin/python auxiliary_overlap/finish.py",
             "exit": 0, "elapsed_seconds": 1.15,
             "meaning": "figure label correction only; no further LP"},
        ],
        "cumulative_wall_seconds": 32.83,
        "highs_calls": 3, "highs_time_limit_each_seconds": 10,
        "max_observed_RSS_kib": 112940,
        "first_failure_retained": True,
        "validation_evidence": [str(HERE/name) for name in [
            "RUN_TIME.txt", "RUN_STDOUT.txt", "RUN_STDERR.txt", "FIRST_FAILURE.txt",
            "FINISH_TIME.txt", "FINISH_STDOUT.txt", "FINISH_STDERR.txt",
            "TEST_TIME.txt", "TEST_STDOUT.txt", "TEST_STDERR.txt",
            "FINISH2_TIME.txt", "FINISH2_STDOUT.txt", "FINISH2_STDERR.txt"]],
        "scientific_status": "candidate only; independent review required",
        "original_acceptance": "HOLD",
    }
    dump(HERE/"RAW_RECEIPT.json", receipt)
    returned = {
        "task_id": TASK, "packet_id": PACKET,
        "input_identity": manifest["input_identity"], "agent_id": AGENT,
        "outcome": "success", "candidate_identity": candidate,
        "validation_evidence": receipt["validation_evidence"],
        "raw_receipt": str(HERE/"RAW_RECEIPT.json"),
        "qualified_products": [str(HERE/name) for name in [
            "RESULT.json", "joint_tensor_atomic.npz", "figure.png", "REPORT.md"]],
        "claim_status": "conditional_candidate_pending_independent_review",
        "observed_runtime": "UNKNOWN",
    }
    dump(HERE/"RETURN.json", returned)
    print(json.dumps(returned, sort_keys=True))


if __name__ == "__main__":
    main()
