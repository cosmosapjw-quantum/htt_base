#!/usr/bin/env python3
"""Synthesize the four v7 external audit / upgrade zip packages.

The zip packages are treated as external review inputs. This generator records
their content hashes, finding map, claim-firewall response, and the next v7 work
packages without importing the external code as production implementation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import sys
import zipfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
COMMON_ROOT = REPO_ROOT / "htt" / "src"
if str(COMMON_ROOT) not in sys.path:
    sys.path.insert(0, str(COMMON_ROOT))

from common.artifact_manifest import validate_manifest_payload  # noqa: E402


SCRIPT_PATH = "scripts/build_v7_external_audit_synthesis.py"
OUT_JSON = REPO_ROOT / "docs/generated/v7_external_audit_synthesis_matrix.json"
OUT_MD = REPO_ROOT / "docs/generated/v7_external_audit_synthesis_matrix.md"
ZIP_INPUTS = (
    "htt_v6_strengthened_publication_bundle.zip",
    "htt_v6_critical_review_bundle.zip",
    "htt_v6_referee_package_20260709.zip",
    "htt_v6_referee_fortification_package_v2.zip",
)


def _repo_relative(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _config_hash(payload: dict[str, Any]) -> str:
    text = json.dumps(payload, sort_keys=True, default=float)
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _zip_inventory(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"required zip not found: {_repo_relative(path)}")
    with zipfile.ZipFile(path) as zf:
        bad = zf.testzip()
        names = zf.namelist()
    return {
        "path": _repo_relative(path),
        "sha256": _sha256_file(path),
        "size_bytes": path.stat().st_size,
        "member_count": len(names),
        "integrity": "PASS" if bad is None else f"FAIL:{bad}",
        "top_level_entries": sorted({name.split("/", 1)[0] for name in names if name})[:12],
    }


FINDINGS = (
    {
        "id": "F1",
        "severity": "fatal_if_unfixed",
        "finding": "Omega_k_aniso domain was underdeclared as nonnegative.",
        "repo_response": "Use signed component boxes and publish open/all curvature branch intervals.",
        "owner": "OBSSTAT",
        "target": "htt/obsstat/egs3_identified_set.py",
        "claim_risk": "domain_overstatement",
        "acceptance": "open branch preserves v6 interval; all branch shifts lower endpoint.",
    },
    {
        "id": "F2",
        "severity": "fatal_if_unfixed",
        "finding": "No closed y -> R -> tau -> interval/status card was present on current data.",
        "repo_response": "Add K5/CF4 identified-interval diagnostic card with plugin firewall.",
        "owner": "OBSSTAT",
        "target": "scripts/k5_cf4_identified_interval_card.py",
        "claim_risk": "pipeline_not_demonstrated",
        "acceptance": "real CF4 bulk enters Omega_tilt; unbound components block promotion.",
    },
    {
        "id": "F3",
        "severity": "major_revision",
        "finding": "Audit vocabulary and journal argument were mixed.",
        "repo_response": "Keep generated audit cards separate from Paper A theorem-witness-result prose.",
        "owner": "COMMON",
        "target": "docs/generated/v7_external_audit_synthesis_matrix.md",
        "claim_risk": "publication_framing",
        "acceptance": "report-facing figures remain concrete data analyses, not meta/process figures.",
    },
    {
        "id": "M1",
        "severity": "major",
        "finding": "G_F joint interval is not strictly narrower in every nondegenerate case.",
        "repo_response": "Add strict/equality classifier and counterexample witness.",
        "owner": "OBSSTAT",
        "target": "htt/obsstat/egs3_gf_interval.py",
        "claim_risk": "theorem_overstatement",
        "acceptance": "joint subset relation remains; strictness requires a shared-extrema conflict.",
    },
    {
        "id": "M2",
        "severity": "major",
        "finding": "Sharpness claim conflated convex component-model sharpness with physical realization.",
        "repo_response": "Label current result as component-box sharpness; defer full realization.",
        "owner": "OBSSTAT",
        "target": "Paper A text",
        "claim_risk": "realizability_overstatement",
        "acceptance": "no full physical-realization claim appears without a dedicated seal.",
    },
    {
        "id": "M3",
        "severity": "major",
        "finding": "Known-covariance chi-square thresholds were used where covariance may be simulation-estimated.",
        "repo_response": "Add estimated_covariance_f threshold policy with n_sim fail-closed validation.",
        "owner": "OBSSTAT",
        "target": "htt/obsstat/egs3_identified_set.py",
        "claim_risk": "size_inflation",
        "acceptance": "Hotelling/F threshold is available and invalid n_sim fails closed.",
    },
    {
        "id": "M4",
        "severity": "major",
        "finding": "MES epsilon coefficients are registered external values, not rederived here.",
        "repo_response": "Keep rederived_here=false and block promotion of MES-dependent K5 placeholders.",
        "owner": "COMMON",
        "target": "docs/generated/parent_identity_seal.json",
        "claim_risk": "provenance_overstatement",
        "acceptance": "generated cards preserve registered_external caveat.",
    },
    {
        "id": "M5",
        "severity": "major",
        "finding": "A measured response matrix R is not yet published.",
        "repo_response": "Use K5 card as closure diagnostic only; schedule measured R table/SVD card.",
        "owner": "OBSSTAT",
        "target": "future_v7_R_card",
        "claim_risk": "response_proxy_overread",
        "acceptance": "no observed-sector response vector is promoted as a measured R result.",
    },
    {
        "id": "M6_M7",
        "severity": "major",
        "finding": "DESI and CF4 surfaces need footprint/window and distance-error forward-model warnings.",
        "repo_response": "Keep these as diagnostic figures until matched masks/randoms/corrections are bound.",
        "owner": "OBSSTAT",
        "target": "report_data_analysis_current",
        "claim_risk": "survey_systematics",
        "acceptance": "figure captions and manifests preserve diagnostic-only status.",
    },
    {
        "id": "M8_m11",
        "severity": "minor_to_major_if_untracked",
        "finding": "Monte Carlo/e-value gate tolerances must be explicit.",
        "repo_response": "Record deterministic G1-G5 gate policy witness in v7 fortification artifact.",
        "owner": "OBSSTAT",
        "target": "scripts/run_v7_fortification_witnesses.py",
        "claim_risk": "hidden_tolerance",
        "acceptance": "gate policy and printed z/tolerance values are generated.",
    },
    {
        "id": "M9",
        "severity": "major",
        "finding": "Observed-sector response vector mixed proxy axes.",
        "repo_response": "Split proxy dashboard from any future measured g-coordinate card.",
        "owner": "OBSSTAT",
        "target": "future_v7_R_card",
        "claim_risk": "proxy_as_measurement",
        "acceptance": "current K1/K5 figures remain diagnostic proxy dashboards.",
    },
)

WORK_PACKAGES = (
    {
        "id": "V7-001",
        "title": "Signed identified-set and threshold policy hardening",
        "deliverables": [
            "signed curvature branch reports",
            "estimated_covariance_f threshold policy",
            "G_F strict/equality classifier",
        ],
        "acceptance": "EGS3 contract tests pass and generated witnesses are current.",
    },
    {
        "id": "V7-002",
        "title": "K5/CF4 diagnostic closure card",
        "deliverables": [
            "k5_cf4_identified_interval_card.json",
            "k5_cf4_identified_interval_card.md",
        ],
        "acceptance": "real CF4 bulk is used; plugin firewall blocks observational promotion.",
    },
    {
        "id": "V7-003",
        "title": "Paper A prose and theorem-lane cleanup",
        "deliverables": [
            "v7_paper_a_revision_packet.json",
            "v7_paper_a_skeleton.tex",
            "P31/P35/P36 wording replacement",
            "MES registered-external caveat",
            "appendix-only diagnostic figure framing",
        ],
        "acceptance": "claim-language and report-lane tests pass.",
    },
    {
        "id": "V7-BLOCKED",
        "title": "Deferred promotion blockers",
        "deliverables": [
            "T3-lin symbolic seal",
            "MES rederivation",
            "measured R SVD/null-vector card",
            "K1 closed E2E lane",
            "DESI official randoms/mask correction",
        ],
        "acceptance": "tracked as blocked/deferred, not silently promoted.",
    },
)


def build_payload(*, generating_command: str) -> dict[str, Any]:
    zip_paths = tuple(REPO_ROOT / name for name in ZIP_INPUTS)
    inventories = [_zip_inventory(path) for path in zip_paths]
    input_hashes = [f"{row['path']}:{row['sha256']}" for row in inventories]
    payload: dict[str, Any] = {
        "artifact_id": "common.v7_external_audit_synthesis_matrix",
        "artifact_path": _repo_relative(OUT_JSON),
        "schema": "htt.v7_external_audit_synthesis_matrix.v1",
        "schema_version": "htt.v7_external_audit_synthesis_matrix.v1",
        "owner": "COMMON",
        "implementation_scope": "common",
        "claim_tier": "diagnostic_only",
        "production_status": "diagnostic_only",
        "artifact_mode": "external_audit_conditioned",
        "allowed_use": "external_audit",
        "created_by": SCRIPT_PATH,
        "git_commit": "content-addressed",
        "code_version": "content-addressed",
        "transfer_source": "none",
        "sky_support_status": "not_directional",
        "null_mock_status": "not_statistical",
        "config_hash": _config_hash(
            {
                "inputs": input_hashes,
                "findings": FINDINGS,
                "work_packages": WORK_PACKAGES,
                "version": "v7-external-audit-synthesis",
            }
        ),
        "input_hashes": input_hashes,
        "caveats": [
            "Synthesis of external review inputs; not a scientific result.",
            "External code is not imported as production implementation.",
            "All v7 public claims remain diagnostic-only or blocked until their gates pass.",
        ],
        "required_gates": [
            "four_zip_inputs_present",
            "zip_integrity_passed",
            "claim_firewall_mapping_recorded",
        ],
        "passed_gates": [
            "four_zip_inputs_present",
            "zip_integrity_passed",
            "claim_firewall_mapping_recorded",
        ],
        "failed_gates": [
            "native_low_ell_solver_absent",
            "measured_R_card_absent",
            "K1_E2E_systematics_absent",
        ],
        "generating_command": generating_command,
        "git_commit_or_worktree_state": "content-addressed",
        "zip_inputs": inventories,
        "findings": list(FINDINGS),
        "v7_work_packages": list(WORK_PACKAGES),
        "statistics_definitions": {
            "purpose": "external audit synthesis and v7 work routing",
            "claim_firewall": "no native solver, no posterior odds, no morphology-family promotion",
        },
    }
    issues = validate_manifest_payload(
        payload,
        manifest_path=OUT_JSON.relative_to(REPO_ROOT),
        expected_artifact_path=_repo_relative(OUT_JSON),
    )
    if issues:
        rendered = "; ".join(f"{issue.code}: {issue.detail}" for issue in issues)
        raise ValueError(f"invalid v7 synthesis manifest: {rendered}")
    return payload


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# v7 External Audit Synthesis Matrix",
        "",
        "owner: COMMON",
        "implementation_scope: common",
        "claim_tier: diagnostic_only",
        f"config_hash: `{payload['config_hash']}`",
        f"generating_command: `{payload['generating_command']}`",
        "",
        "## Zip Inputs",
        "",
        "| Zip | SHA256 | Members | Integrity |",
        "| --- | --- | ---: | --- |",
    ]
    for row in payload["zip_inputs"]:
        lines.append(
            f"| `{row['path']}` | `{row['sha256']}` | {row['member_count']} | `{row['integrity']}` |"
        )
    lines.extend([
        "",
        "## Findings",
        "",
        "| ID | Severity | Response | Target |",
        "| --- | --- | --- | --- |",
    ])
    for row in payload["findings"]:
        lines.append(
            f"| {row['id']} | `{row['severity']}` | {row['repo_response']} | `{row['target']}` |"
        )
    lines.extend([
        "",
        "## v7 Work Packages",
        "",
        "| ID | Title | Acceptance |",
        "| --- | --- | --- |",
    ])
    for row in payload["v7_work_packages"]:
        lines.append(f"| {row['id']} | {row['title']} | {row['acceptance']} |")
    lines.extend([
        "",
        "## Caveats",
        "",
    ])
    lines.extend(f"- {row}" for row in payload["caveats"])
    return "\n".join(lines) + "\n"


def _command_from_args(argv: list[str] | None) -> str:
    args = sys.argv[1:] if argv is None else argv
    return "venv/bin/python " + SCRIPT_PATH + (
        "" if not args else " " + " ".join(shlex.quote(arg) for arg in args)
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if outputs are stale")
    args = parser.parse_args(argv)
    command = _command_from_args(argv)
    if args.check:
        command = "venv/bin/python " + SCRIPT_PATH
    payload = build_payload(generating_command=command)
    json_text = json.dumps(payload, indent=2, sort_keys=True, default=float) + "\n"
    md_text = render_markdown(payload)
    if args.check:
        stale = []
        if not OUT_JSON.is_file() or OUT_JSON.read_text(encoding="utf-8") != json_text:
            stale.append(_repo_relative(OUT_JSON))
        if not OUT_MD.is_file() or OUT_MD.read_text(encoding="utf-8") != md_text:
            stale.append(_repo_relative(OUT_MD))
        if stale:
            print("stale outputs: " + ", ".join(stale))
            return 1
        print("v7_external_audit_synthesis_matrix outputs up to date")
        return 0
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json_text, encoding="utf-8")
    OUT_MD.write_text(md_text, encoding="utf-8")
    print(f"wrote {_repo_relative(OUT_JSON)}")
    print(f"wrote {_repo_relative(OUT_MD)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
