"""Seal the targeted repair without changing controller-referenced first receipts."""
from __future__ import annotations

import json

from compute import EXPECTED, HERE, INPUT_SHA, PACKET, TASK, digest

FIRST_CANDIDATE = "sha256:1c2aa2d75979e9d534ee2dcc4ea790bb62146320f75b2f27143d0a354a947d08"
FIRST_RAW_SHA = "cb456da1545f3bebdb56285a9b75e25643a99a06117438c303ba5b92f001e34c"
FILES = ["compute.py", "test_compute.py", "finalize.py", "RESULT.json",
         "RESPONSE_GEOMETRY.png", "REPORT.md", "REPAIR_RUN_STDOUT.txt",
         "REPAIR_RUN_STDERR.txt", "REPAIR_TEST_STDOUT.txt", "REPAIR_TEST_STDERR.txt",
         "REPAIR_FIRST_FAILURE.txt"]


def main():
    if f"sha256:{digest(HERE/'first_candidate/MANIFEST.json')}" != FIRST_CANDIDATE:
        raise ValueError("first candidate archive changed")
    if digest(HERE/"RAW_RECEIPT.json") != FIRST_RAW_SHA:
        raise ValueError("controller-referenced first raw receipt changed")
    if (HERE/"RETURN.json").read_bytes() != (HERE/"first_candidate/RETURN.json").read_bytes():
        raise ValueError("controller-referenced first return changed")
    result = json.loads((HERE/"RESULT.json").read_text())
    old = json.loads((HERE/"first_candidate/RESULT.json").read_text())
    if result["packet_id"] != PACKET or result["input_identity"] != f"sha256:{INPUT_SHA}":
        raise ValueError("source packet/input binding changed")
    for key in ("scenarios", "cohort", "t1", "response_dictionary_fixed_before_y"):
        if result[key] != old[key]:
            raise ValueError(f"unapproved numerical change in {key}")
    testlog = (HERE/"REPAIR_TEST_STDERR.txt").read_text()
    if "Ran 5 tests" not in testlog or "\nOK\n" not in testlog:
        raise ValueError("five targeted tests did not pass")
    entries = [{"path": name, "sha256": digest(HERE/name), "bytes": (HERE/name).stat().st_size}
               for name in FILES]
    manifest = {"task_id":TASK, "base_packet_id":PACKET,
        "repair_packet_id":"PENDING_ACTUAL_CONTROLLER_PACKET",
        "input_identity":f"sha256:{INPUT_SHA}", "base_candidate_identity":FIRST_CANDIDATE,
        "owner":"HTT observational method", "scope":"one reviewer-authorized optical-law premise correction",
        "claim_tier":"C0_CONDITIONAL_DIAGNOSTIC",
        "source_identity":[{"path":str(path),"sha256":expected} for path,expected in EXPECTED.items()],
        "original_raw_receipt_sha256":FIRST_RAW_SHA,
        "numerical_arrays_unchanged":{"scenarios":True,"cohort":True,"t1":True,
                                      "response_dictionary_fixed_before_y":True},
        "files":entries,"candidate_identity_definition":"sha256 of this REPAIR_MANIFEST.json exact bytes"}
    path = HERE/"REPAIR_MANIFEST.json"
    path.write_text(json.dumps(manifest,indent=2,allow_nan=False)+"\n")
    candidate = f"sha256:{digest(path)}"
    receipt = {"task_id":TASK,"base_packet_id":PACKET,
        "repair_packet_id":"PENDING_ACTUAL_CONTROLLER_PACKET",
        "input_identity":f"sha256:{INPUT_SHA}","base_candidate_identity":FIRST_CANDIDATE,
        "candidate_identity":candidate,"agent_id":"/root/rc_047ec280a16abca8",
        "requested_runtime":"gpt-6-sol/high","observed_runtime":"UNKNOWN",
        "cwd":str(HERE),"commands":[
            {"command":"python compute.py > REPAIR_RUN_STDOUT.txt 2> REPAIR_RUN_STDERR.txt","exit_code":0},
            {"command":"python -m unittest -v test_compute.py > REPAIR_TEST_STDOUT.txt 2> REPAIR_TEST_STDERR.txt","exit_code":0},
            {"command":"python finalize.py","exit_code":0}],
        "validation_evidence":[
            "five focused tests pass including finite q=0.1 non-dipole counterexample and q->0 limit",
            "all original scenario matrices, angles, ranks, coefficient/covariance arrays, cohort, T1 witness and response basis exactly equal archived first result",
            "first candidate manifest, controller RAW_RECEIPT and RETURN bytes preserved",
            "317 km/s physical-domain failure retained; scientific admission HOLD"],
        "first_repair_failure":"REPAIR_FIRST_FAILURE.txt retains initial too-strict finite-q zero-limit assertion; adjusted analytic-order test, no numerical fit changed",
        "original_raw_receipt_sha256":FIRST_RAW_SHA,"scientific_admission":"HOLD",
        "original_acceptance_met":False,"independent_repair_review":"PENDING",
        "candidate_manifest":str(path),"candidate_manifest_sha256":digest(path)}
    raw=HERE/"REPAIR_RAW_RECEIPT.json"
    raw.write_text(json.dumps(receipt,indent=2,allow_nan=False)+"\n")
    print(candidate)


if __name__ == "__main__":
    main()
