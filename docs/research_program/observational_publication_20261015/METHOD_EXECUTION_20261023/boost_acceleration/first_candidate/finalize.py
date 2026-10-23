"""Seal the R24 candidate and packet-bound raw return after successful validation."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from compute import EXPECTED, HERE, INPUT_SHA, PACKET, TASK, digest

FILES = ["compute.py", "test_compute.py", "finalize.py", "RESULT.json",
         "RESPONSE_GEOMETRY.png", "REPORT.md", "RUN_STDOUT.txt", "RUN_STDERR.txt",
         "FIRST_FAILURE.txt", "TEST_STDOUT.txt", "TEST_STDERR.txt"]


def main():
    result = json.loads((HERE / "RESULT.json").read_text())
    if result["packet_id"] != PACKET or result["input_identity"] != f"sha256:{INPUT_SHA}":
        raise ValueError("result packet/input binding changed")
    testlog = (HERE / "TEST_STDERR.txt").read_text()
    if "Ran 3 tests" not in testlog or "OK" not in testlog:
        raise ValueError("focused tests did not pass")
    entries = [{"path": name, "sha256": digest(HERE/name), "bytes": (HERE/name).stat().st_size}
               for name in FILES]
    manifest = {"task_id": TASK, "packet_id": PACKET, "input_identity": f"sha256:{INPUT_SHA}",
        "owner": "HTT observational method", "scope": "conditional response quotient only",
        "claim_tier": "C0_CONDITIONAL_DIAGNOSTIC", "source_identity":
        [{"path": str(path), "sha256": expected} for path,expected in EXPECTED.items()],
        "files": entries,
        "candidate_identity_definition": "sha256 of this MANIFEST.json exact bytes"}
    path = HERE / "MANIFEST.json"
    path.write_text(json.dumps(manifest, indent=2, allow_nan=False)+"\n")
    candidate = f"sha256:{digest(path)}"
    receipt = {"task_id": TASK, "packet_id": PACKET, "input_identity": f"sha256:{INPUT_SHA}",
        "candidate_identity": candidate, "agent_id": "/root/rc_047ec280a16abca8",
        "requested_runtime": "gpt-6-sol/high", "observed_runtime": "UNKNOWN",
        "cwd": str(HERE), "commands": [
            {"command":"python compute.py > RUN_STDOUT.txt 2> RUN_STDERR.txt","exit_code":0},
            {"command":"python -m unittest -v test_compute.py > TEST_STDOUT.txt 2> TEST_STDERR.txt","exit_code":0},
            {"command":"python finalize.py","exit_code":0}],
        "first_failure": "Initial manifest key mismatch before computation; FIRST_FAILURE.txt retained; repaired to frozen files key",
        "validation_evidence": [
            "274 released/628 selected/354 undefined; PGC9031 at 317 km/s retained",
            "four full authored covariance scenarios; full baseline and five STF nuisance columns",
            "nuisance-profiled rank 12/15 at 1e-8, 1e-10, 1e-12; three exact duplicate null directions",
            "three actual-cohort canonical angles and conditional coefficient/covariance matrices per scenario",
            "dense 274-row Schur information reference agrees at rtol 1e-10, atol 1e-12",
            "synthetic fixed-H optical dipole units and T1 PSD perturbation bound",
            "three focused unittest tests pass; 2D figure generated"],
        "scientific_admission": "HOLD", "original_acceptance_met": False,
        "physical_domain_failure": "PGC9031 317 km/s; reviewed union flow fraction 2.261954-2.445192",
        "independent_review": "PENDING", "source_hashes_checked": len(EXPECTED),
        "candidate_manifest": str(path), "candidate_manifest_sha256": digest(path)}
    raw = HERE / "RAW_RECEIPT.json"
    raw.write_text(json.dumps(receipt, indent=2, allow_nan=False)+"\n")
    answer = {"task_id": TASK, "phase": "execute", "attempt": 1,
        "packet_id": PACKET, "input_identity": f"sha256:{INPUT_SHA}",
        "candidate_identity": candidate, "agent_id": "/root/rc_047ec280a16abca8",
        "raw_receipt": str(raw), "artifact_manifest": str(path),
        "result": str(HERE/"RESULT.json"), "report": str(HERE/"REPORT.md"),
        "figure": str(HERE/"RESPONSE_GEOMETRY.png"), "outcome": "success",
        "completed": "Same-274-row, four-covariance nuisance-profiled constant/K/fixed-depth response quotient; exact optical angular-calibration degeneracy and T1 synthetic algebraic witness",
        "validation_evidence": receipt["validation_evidence"],
        "scientific_admission": "HOLD", "original_acceptance_met": False,
        "independent_review": "PENDING", "requested_runtime": "gpt-6-sol/high",
        "observed_runtime": "UNKNOWN", "no_dispatch_claim": True,
        "next_checkpoint": "Independent nonauthor candidate-bound review; actual energy-frame epsilon/P/g/tracer map, full observer transformation, physically valid low-velocity domain and covariance remain missing"}
    (HERE / "RETURN.json").write_text(json.dumps(answer, indent=2, allow_nan=False)+"\n")
    print(candidate)


if __name__ == "__main__":
    main()
