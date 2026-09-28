#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[2]
OLD = HERE.parent / "typefree_loop2_20260928"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    corrections = []
    for correction_id, old_rel, new_rel, statement, status, caveat in (
        ("F1", "TF_W1_INPUT_KO.md", "ERRATA_F1_W1_KO.md", "Restrict the kernel criterion to unconstrained linear/affine variations and use feasible fibre images on general K.", "DERIVED", "Does not supply the missing source/time law or observational calibration."),
        ("F2", "db/apply_append.py", "db/safe_append.py", "Use a read-only hash-pinned source, preflight exclusive outputs, alias rejection, transactional append and measured source immutability.", "VALIDATED", "Historical migration scripts and outputs remain unchanged."),
        ("F3", "db/append_final_evidence.py", "ERRATA_F3_LEAN_SCOPE_KO.md", "Read gap_column3 as one three-component column plus a separate explicit 3x3 identity.", "VALIDATED", "This is a scope/provenance correction, not a new Lean proof."),
    ):
        old_path, new_path = OLD/old_rel, HERE/new_rel
        corrections.append({
            "correction_id": correction_id, "supersedes_path": str(old_path.relative_to(ROOT)),
            "supersedes_sha256": sha(old_path), "statement": statement, "status": status,
            "artifact_path": str(new_path.relative_to(ROOT)), "artifact_sha256": sha(new_path), "caveat": caveat,
        })
    (HERE/"CORRECTIONS.json").write_text(json.dumps({"corrections": corrections}, ensure_ascii=False, sort_keys=True, indent=2)+"\n", encoding="utf-8")
    audit = HERE / "EXTERNAL_AUDIT_RECORD.json"
    review_status = HERE / "INDEPENDENT_REVIEW_STATUS.json"
    reviews = [
        {
            "review_id": "LOOP2-AUDIT-20260928", "reviewer_role": "external_independent_audit",
            "status": "FAIL_CORRECTIONS_REQUIRED", "scope": "published bytes plus F1-F4 audit",
            "artifact_path": str(audit.relative_to(ROOT)), "artifact_sha256": sha(audit),
            "caveat": "Pre-correction audit; launch evidence unverified and execution evidence self-declared.",
        },
        {
            "review_id": "LOOP2-FOLLOWUP-20260929", "reviewer_role": "registered_unlaunched_reviewer",
            "status": "INCONCLUSIVE_REVIEW_AUTHOR_ATTESTATION_MISSING", "scope": "F1-F3 correction follow-up",
            "artifact_path": str(review_status.relative_to(ROOT)), "artifact_sha256": sha(review_status),
            "caveat": "Assignment was registered but not launched because the router required actual author model/effort attestation; no independent PASS is claimed.",
        },
    ]
    (HERE/"REVIEWS.json").write_text(json.dumps({"reviews": reviews}, ensure_ascii=False, sort_keys=True, indent=2)+"\n", encoding="utf-8")


if __name__ == "__main__":
    main()
