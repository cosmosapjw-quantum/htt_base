"""Seal the bounded P6-IR-01 repair candidate from actual local receipts."""
from pathlib import Path
import hashlib
import json


R = Path(__file__).resolve().parent
REPORT = R / "report"
RAW = REPORT / "raw"
BASE = R.parent
REPO = Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
PACKET = Path("/mnt/extdrive/workdir/htt_open_data/r35_publication_acceleration_controller/NEXT_AFTER_BP_REPAIRED_REVIEW.json")
ACK = Path("/mnt/extdrive/workdir/htt_open_data/r35_publication_acceleration_controller/P6_REPAIR_ACTUAL_ACK_GO.json")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, obj):
    path.write_text(json.dumps(obj, indent=2, allow_nan=False) + "\n")


packet = json.loads(PACKET.read_text())
ack = json.loads(ACK.read_text())
assert packet["packet_id"] == ack["packet_id"] == "9c3ccfd20d64ff55c67e5f0c3aad1852d1bcb0f4a7c25b95f698b2deb9721db3"
assert packet["task_id"] == "R32-05-P6-OPTICAL"
assert packet["input_identity"] == ack["input_identity"] == "sha256:f900ec93d972751795cdd825ee0f362eabed3a2aae60b59e4c24d265ee6ec132"
assert ack["agent_id"] == "/root/rc_9c3ccfd20d64ff55" and ack["go"] and ack["acknowledged"]
assert packet["candidate_identity"] == "sha256:341346452c546de7877bf839bde8e583e37c8c461703469644ab7675edba1bfd"
assert sha(BASE / "report/RESULT.json") == "343622f6bed1197dd0e08b7c64fbfabefba74f5ec02baf9a51b839dda97ae9b3"
assert sha(BASE / "science/MANUSCRIPT.md") == "4836adcfeda1f7b231e98a91ece8479f223d5b8a11762776a0aeef1fa2ada7ea"
assert sha(BASE / "report/main.tex") == "6442cd7269b7fb1ead59468d5f1301490b7c20e932b8fd05fae504c8331f57ef"
assert sha(R / "science/MANUSCRIPT.md") == "ee6d35bd8b4b571b7ec672b809d10df6b0f5c981dbf0c6d1bc88fa3b77eb59e1"
assert sha(REPORT / "main.tex") == "4bb9ef46647f77baee40d6c9254ff8939caa2b0dde407fbe0135a7e8bdf95704"

receipt_names = ("regression", "source_build", "latexmk", "pdftotext", "pdfinfo", "candidate_audit")
receipts = {name: json.loads((RAW / f"{name}_receipt.json").read_text()) for name in receipt_names}
assert all(x["exit_code"] == 0 for x in receipts.values())
inspection = json.loads((RAW / "visual_inspection.json").read_text())
audit = json.loads((REPORT / "generated/candidate_audit.json").read_text())
assert inspection["page_count"] == audit["pages"] == 13
assert audit["equation_tags"] == 35 and audit["observable_map_dimensionless_crosscheck"]
assert audit["forbidden_phrase_scan"] == "PASS" and audit["overfull_boxes"] == 0
assert sha(R / "report/generated/retained_tensor_region.json") == sha(BASE / "report/generated/retained_tensor_region.json")
reused = json.loads((RAW / "reuse_parity.json").read_text())
assert reused["prior_checks_reused_count"] == 61 and reused["consumer_runs_this_repair"] == 0
assert len(reused["artifacts"]) == 9
assert all(sha(Path(x["base_path"])) == sha(Path(x["repair_path"])) == x["sha256"] for x in reused["artifacts"])
assert len(json.loads((REPORT / "generated/claim_to_source.json").read_text())["claims"]) == 9
source_list = json.loads((REPORT / "generated/sources.json").read_text())
assert all(sha(REPO / x["path"]) == x["sha256"] for x in source_list)

commands = [dict(stage=k, **v) for k, v in receipts.items()]
commands.append({"stage": "inspection_render", "receipt_path": str(RAW / "inspection_render.json"), "exit_codes": [x["exit_code"] for x in json.loads((RAW / "inspection_render.json").read_text())]})
commands.append({"stage": "packaging_first_failure", "receipt_path": str(RAW / "packaging_first_failure.json"), "exit_code": 1, "resolved": True})
commands.append({"stage": "package_repair", "command": ["python", "package_repair.py"], "cwd": str(R), "exit_code": 0, "note": "Exit verified by caller after RESULT and manifest identity are printed."})
save(RAW / "commands.json", commands)
save(RAW / "repair_receipt.json", {
    "schema": "htt.p6.repair_execution_receipt/1",
    "packet_id": packet["packet_id"], "task_id": packet["task_id"], "input_identity": packet["input_identity"],
    "actual_agent_id": ack["agent_id"], "base_candidate_identity": packet["candidate_identity"],
    "base_result_sha256": sha(BASE / "report/RESULT.json"), "science_source_sha256": sha(R / "science/MANUSCRIPT.md"),
    "tex_source_sha256": sha(REPORT / "main.tex"), "actual_exits": {k: v["exit_code"] for k, v in receipts.items()},
    "regression_tests": 3, "prior_numerical_checks_reused": 61, "numerical_consumer_runs_in_repair": 0,
    "prior_artifacts_byte_exact_reused": len(reused["artifacts"]), "actual_pdf_pages": inspection["page_count"],
    "changed_pages_inspected": inspection["pages_inspected_visually"],
    "layout_observation": inspection["observations"][-1],
    "remaining_latex_warning": audit["remaining_warnings"],
    "first_packaging_failure_retained": str(RAW / "packaging_first_failure.json"),
    "scope": "P6-IR-01 empty-image feasibility guard and proof; approved literal scientific source hashes retained.",
    "acceptance_passed": False, "original_acceptance_passed": False, "qualified_products": [],
})

outputs = []
for path in sorted(R.rglob("*")):
    if path.is_file() and path != REPORT / "RESULT.json":
        outputs.append({"path": str(path.relative_to(R)), "sha256": sha(path), "bytes": path.stat().st_size})
manifest = {"sources": source_list, "outputs": outputs}
identity = hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
base_result = json.loads((BASE / "report/RESULT.json").read_text())
result = {
    "schema": "htt.p6.optical_inverse_repair_candidate/1", "task_id": packet["task_id"],
    "packet_id": packet["packet_id"], "campaign": packet["campaign"], "attempt": packet["attempt"],
    "phase": packet["phase"], "assignment_input_identity": packet["input_identity"],
    "base_candidate_identity": packet["candidate_identity"], "candidate_path": str(REPORT),
    "candidate_only": True, "acceptance_met": False, "acceptance_passed": False,
    "original_acceptance_passed": False, "original42_promoted": False, "qualified_products": [],
    "proposed_qualified_products": ["optical_inverse_note"],
    "owner": "mio", "scope": "Conditional finite optical inverse methods and retained apparent tensor diagnostic",
    "claim_tier": "C0", "transfer_source": "none (retained apparent CF4 statistic empirical_proxy)",
    "requested_executor": {"model": "gpt-6-sol", "reasoning_effort": "high"},
    "observed_executor": "UNKNOWN", "actual_agent_id": ack["agent_id"],
    "repair_status": "P6_IR_01_APPLIED_PENDING_FRESH_INDEPENDENT_REVIEW",
    "build_status": "BUILT_CANDIDATE_PENDING_FRESH_INDEPENDENT_REVIEW",
    "consumer_run_count_this_repair": 0, "prior_focused_checks_reused": 61,
    "new_feasibility_regression_tests_passed": 3, "candidate_audit": audit,
    "diagnostic_statuses": base_result["diagnostic_statuses"],
    "sky_support_status": base_result["sky_support_status"], "null_mock_status": base_result["null_mock_status"],
    "limitations": base_result["limitations"] + ["Exact approved source compiles to 13 pages; final page has four readable retained-source endnote lines. Publication layout remains pending."],
    "manifest_canonical_json_sha256": identity, "manifest": manifest,
}
save(REPORT / "RESULT.json", result)
print(json.dumps({"result_path": str(REPORT / "RESULT.json"), "result_sha256": sha(REPORT / "RESULT.json"),
                  "manifest_canonical_json_sha256": identity, "output_files": len(outputs), "pages": audit["pages"]}, indent=2))
