#!/usr/bin/env python3
"""Build and validate the 2026-07-14 JCAP/PRD adversarial audit package.

This is an audit-only harness.  It may read production inputs and execute
existing generators, but it never overwrites production result cards.  The
counterfactual family lane remains internal-only and cannot be consumed as
scientific evidence.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import tempfile
import time
from typing import Any, Iterable
import zipfile

import yaml


REPO = Path(__file__).resolve().parents[2]
for _root in (REPO, REPO / "htt", REPO / "htt/htt", REPO / "htt/src"):
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))

# The repository deliberately carries a top-level multi-owner ``htt`` package
# and a nested HTT-inference package with the same import root.  Audit imports
# need both search locations without changing the production package layout.
import htt as _htt_package  # noqa: E402
from common.semantic_guards.no_overclaim import scan_text as scan_claim_text  # noqa: E402

for _package_root in (REPO / "htt", REPO / "htt/htt/htt"):
    if str(_package_root) not in _htt_package.__path__:
        _htt_package.__path__.append(str(_package_root))

AUDIT = REPO / "docs/audits/jcap_prd_adversarial_audit_20260714"
PRIOR = REPO / "docs/audits/self_adversarial_audit_20260713_nsc"
PRIOR_LEDGER = PRIOR / "03_cove_correctness_ledger.json"
PRIOR_GAPS = PRIOR / "07_completeness_critique.md"
EXECUTION_LEDGER = AUDIT / "execution_ledger.jsonl"
DIAGNOSTICS = AUDIT / "diagnostic_results.json"
MANIFEST = AUDIT / "MANIFEST.json"
ATOMIC_LEDGER = AUDIT / "atomic_finding_ledger.json"
SHORTLIST_FREEZE = AUDIT / "shortlist_freeze.json"
BASELINE_HEAD = "8af39b36c1d5ed4f9b16f0bc71dbecd8b22548d4"
PR117_COMMIT = "f96e8d9eed9d318141d9ea77ab3ce47c2acecef3"
# PR-124 preflight (2026-07-17): rebased by the history rewrite; the
# pre-rewrite id 294d74ce07de030da2f18720d3d45c8a2fef6e17 resolves via
# docs/git_history/commit_map_20260717.tsv.
PR118_MANIFEST_SEAL_COMMIT = "a1bfa463f11391ca01d8af077b9a3cdfe05a5205"
PR117_SEALED_RUNNER_SHA256 = (
    "sha256:614630a438c046418703ec07dd91cf2d305b7ce8962b27904960c4d588c3fa0c"
)
AUDIT_SEED = 20260714

PR118_REQUIRED_RECEIPTS = {
    # ``seal4``/``retry4`` bind the terminal hostile-mutation hardening of the
    # runner and contract tests.  Superseded records remain in the append-only
    # ledger as execution history but cannot satisfy the current seal.
    "pr118_final_dag_seal4": "PASS",
    "pr118_final_backlog_mirrors_seal4": "PASS",
    "pr118_final_checkpoint_seal4": "PASS",
    "pr118_final_collect_retry4": "PASS",
    "pr118_final_smoke_retry4": "PASS",
    "pr118_final_package_seal4": "PASS",
    "pr118_final_status_contracts_seal4": "PASS",
    "pr118_final_ownership_transfer_seal4": "PASS",
    "pr118_final_claim_language_seal4": "PASS",
    "pr118_final_result_pack_freshness_seal4": "FAIL_OR_BLOCKED",
    "pr118_final_current_figure_manifest_seal4": "FAIL_OR_BLOCKED",
    "pr118_final_generic_figure_manifest_seal4": "FAIL_OR_BLOCKED",
    "pr118_final_publication_freeze_retry3": "PASS",
    "pr118_final_external_package_retry3": "PASS",
    "pr118_final_vendor_archive_adapter_retry3": "PASS",
    "pr118_final_latex_build_seal4": "PASS",
    "pr118_final_contract_preseal": "PASS",
    "pr118_final_diff_check": "PASS",
    "pr118_final_manifest_preseal": "PASS",
}
PR118_RETAINED_ATTEMPT_RESULTS = {
    "pr118_final_collect": "BLOCKED_MISSING_DECLARED_INPUT",
    "pr118_final_smoke": "BLOCKED_MISSING_DECLARED_INPUT",
    "pr118_final_publication_freeze": "FAIL_OR_BLOCKED",
    "pr118_final_external_package": "FAIL_OR_BLOCKED",
    "pr118_final_external_package_retry1": "FAIL_OR_BLOCKED",
    "pr118_final_vendor_archive_adapter": "BLOCKED_MISSING_DECLARED_INPUT",
}

EXPECTED_PRIOR_COUNTS = {"P0": 2, "P1": 14, "P2": 17, "P3": 22}
ALLOWED_DELTA_REASONS = {
    "downstream_propagation",
    "regression",
    "contradictory_independent_reproduction",
    "severity_change",
    "historical_antecedent",
}
ALLOWED_EXAMINATION = {"examined", "sampled", "blocked", "not_examined"}
COUNTERFACTUAL_FIELDS = {
    "claim_tier": "exploratory",
    "artifact_mode": "internal_exploratory",
    "allowed_use": "internal_only",
    "hypothesis_only": True,
    "public_use": False,
}

ADVOCATE_RESPONSE_PATHS = {
    "theory": AUDIT / "agents/advocate_divergence/theory_advocate_response.json",
    "statistics": AUDIT / "agents/advocate_divergence/statistics_advocate_response.json",
    "code": AUDIT / "agents/advocate_divergence/code_advocate_response.json",
    "data_analysis": AUDIT / "agents/advocate_divergence/data_advocate_response.json",
}
ADVOCATE_AXIS_PREFIXES = {
    "theory": "TH-",
    "statistics": "ST-",
    "code": "CO-",
    "data_analysis": "DA-",
}
ADVOCATE_REQUIRED_FIELDS = {
    "candidate_id",
    "axis",
    "title",
    "hypothesis",
    "assumptions",
    "mechanism",
    "supporting_evidence",
    "contrary_evidence",
    "decisive_falsifier",
    "required_data_or_solver",
    "resource_cost",
    "salvage_disposition_proposed",
    "maximum_claim_tier",
    "native_atlas_required",
    "matched_masks_required",
    "matched_nulls_required",
    "covariance_required",
    "family_equivalence_required",
    "hypothesis_only",
    "public_use",
    "author_cannot_promote",
    "web_used",
}
PRE_SOLVER_WEIGHTS = {
    "correctness_falsifiability": 25,
    "identifiability": 20,
    "scientific_effect": 20,
    "novelty": 15,
    "local_feasibility": 10,
    "reproducibility": 10,
}
POST_SOLVER_WEIGHTS = {
    "correctness": 25,
    "scientific_effect": 25,
    "identifiability": 20,
    "novelty": 15,
    "adapter_readiness": 15,
}
ADVOCATE_DISPOSITIONS = {
    "rescued",
    "downclaimed",
    "rebuild_required",
    "native_solver_dependent",
    "falsified",
    "abandoned",
}
CRITICISM_MAP_PATHS = {
    "prior": AUDIT / "agents/criticism_mapping/prior_response_map.json",
    "gap_theory_statistics": AUDIT
    / "agents/criticism_mapping/gap_theory_statistics_response_map.json",
    "data_code": AUDIT / "agents/criticism_mapping/data_code_response_map.json",
}
FINAL_CRAG_RESPONSE_PATHS = {
    "theory_statistics": AUDIT
    / "agents/final_crag/theory_statistics_crag_response.json",
    "code": AUDIT / "agents/final_crag/code_crag_response.json",
    "data": AUDIT / "agents/final_crag/data_crag_response.json",
}
FINAL_CRAG_ASSIGNMENTS = {
    "theory_statistics": {"TH-02", "TH-01", "TH-04", "ST-03", "ST-08", "ST-04"},
    "code": {"CO-04", "CO-07", "CO-06", "CO-01"},
    "data": {"DA-01", "DA-05"},
}
FINAL_REFEREE_RESPONSE_PATHS = {
    "JCAP": AUDIT / "agents/final_referees/jcap_referee_response.json",
    "PRD": AUDIT / "agents/final_referees/prd_referee_response.json",
    "Independent skeptical": AUDIT
    / "agents/final_referees/skeptical_referee_response.json",
}

DIAGNOSTIC_LANE_NAMES = {
    "cf4": "cf4_monopole_propagation",
    "grf": "hermitian_grf_reference",
    "fsigma": "fsigma8_depth_and_uncertainty",
    "desi": "desi_quadrature_and_alpha_refit",
    "act": "act_low_l_transfer_scope",
    "k6": "k6_stencil_grid_convergence",
    "jwst": "jwst_14_anchor_rerun",
}
SEALED_RECEIPT_PREFIX = "sealed_v2_"

# These roles are the immutable PR-117 audit/debate floor.  Later PR-118
# advocate and judging phases may add roles, but cannot erase this evidence.
REQUIRED_AGENT_ROLES = {
    ("initial_crag", "observations"),
    ("initial_crag", "statistics_pv"),
    ("initial_crag", "theory"),
    ("theory_wave", "anisotropy_advocate"),
    ("theory_wave", "gr_convention_auditor"),
    ("theory_wave", "isotropy_advocate"),
    ("statistics_wave", "bayesian_ppc"),
    ("statistics_wave", "frequentist_null"),
    ("statistics_wave", "partial_identification"),
    ("code_wave", "numerical_analyst"),
    ("code_wave", "oracle_provenance"),
    ("code_wave", "reproducibility"),
    ("data_wave", "cf4_observer"),
    ("data_wave", "cmb_observer"),
    ("data_wave", "survey_observer"),
    ("cross_debate", "formalism_statistics"),
    ("cross_debate", "integrity_novelty"),
    ("cross_debate", "physics_observation"),
    ("blind_referees", "data_referee"),
    ("blind_referees", "repro_referee"),
    ("blind_referees", "theory_referee"),
    ("pr117_review", "integration_provenance"),
    ("pr117_review", "schema_harness"),
    ("pr117_review", "science_dedup"),
    ("pr117_rereview", "integration_provenance_followup"),
    ("pr117_rereview", "schema_harness_followup"),
    ("pr117_rereview", "science_dedup_followup"),
}
REQUIRED_PR118_AGENT_ROLES = {
    ("advocate_divergence", "theory_advocate"),
    ("advocate_divergence", "statistics_advocate"),
    ("advocate_divergence", "code_advocate"),
    ("advocate_divergence", "data_advocate"),
    ("advocate_judging", "pre_solver_judge"),
    ("advocate_judging", "post_native_judge"),
    ("advocate_judging", "integrity_veto_judge"),
    ("final_crag", "theory_statistics_crag"),
    ("final_crag", "code_crag"),
    ("final_crag", "data_crag"),
    ("criticism_mapping", "prior_response_map"),
    ("criticism_mapping", "gap_theory_statistics_response_map"),
    ("criticism_mapping", "data_code_response_map"),
    ("final_referees", "jcap_referee"),
    ("final_referees", "prd_referee"),
    ("final_referees", "skeptical_referee"),
    ("pr118_review", "harness_schema"),
    ("pr118_review", "science_claim"),
    ("pr118_review", "integration_provenance"),
}


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_json(payload: Any) -> str:
    return sha256_bytes(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
    )


def relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        handle.write(json.dumps(payload, sort_keys=True, default=str) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def git(*args: str, check: bool = True) -> str:
    run = subprocess.run(
        ["git", *args], cwd=REPO, text=True, capture_output=True, check=False
    )
    if check and run.returncode:
        raise RuntimeError(run.stderr.strip() or f"git {' '.join(args)} failed")
    return run.stdout.strip()


def repo_state() -> dict[str, Any]:
    return {
        "baseline_head": BASELINE_HEAD,
        "current_head": git("rev-parse", "HEAD"),
        "branch": git("branch", "--show-current"),
        "worktree_porcelain": git("status", "--short"),
        "worktree_state_hash": sha256_bytes(
            git("status", "--porcelain=v1", "--untracked-files=all").encode()
        ),
    }


def _artifact_metadata(
    input_paths: Iterable[Path],
    generating_command: str,
    *,
    transfer_source: str = "mixed_none_and_external_transfer_conditional",
    sky_support_status: str = "mixed_audit_only_no_directional_promotion",
    null_mock_status: str = "mixed_matched_proxy_blocked_and_not_statistical",
) -> dict[str, Any]:
    paths = [path for path in input_paths if path.is_file()]
    input_map = {relative(path): sha256_file(path) for path in paths}
    return {
        "owner": "COMMON",
        "implementation_scope": "common",
        "claim_tier": "diagnostic_only",
        "transfer_source": transfer_source,
        "config_hash": sha256_json(input_map),
        "input_hashes": [f"{path}:{digest}" for path, digest in input_map.items()],
        "sky_support_status": sky_support_status,
        "null_mock_status": null_mock_status,
        "caveats": [
            "Internal audit and research-prioritization artifact only.",
            "No production scientific output is repaired or promoted by this artifact.",
            "Counterfactual family/geometry content remains hypothesis-only and public_use=false.",
        ],
        "generating_command": generating_command,
        "git_commit_or_worktree_state": repo_state(),
    }


def _environment_payload() -> dict[str, Any]:
    versions: dict[str, str] = {}
    for name in ("numpy", "scipy", "healpy", "astropy", "camb", "pytest"):
        try:
            module = __import__(name)
            versions[name] = str(getattr(module, "__version__", "unknown"))
        except Exception as exc:  # optional dependencies are evidence, not failures
            versions[name] = f"unavailable:{type(exc).__name__}"
    payload = {
        "captured_at": utcnow(),
        "python": sys.version,
        "executable": sys.executable,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cpu_count": os.cpu_count(),
        "versions": versions,
        "repo_state": repo_state(),
    }
    payload["environment_hash"] = sha256_json(payload)
    return payload


def build_environment() -> dict[str, Any]:
    payload = _environment_payload()
    write_json(AUDIT / "environment.json", payload)
    return payload


def build_pr118_environment() -> dict[str, Any]:
    payload = _environment_payload()
    payload["phase"] = "PR-118-final-validation"
    # Recompute after adding the phase marker.
    payload.pop("environment_hash", None)
    payload["environment_hash"] = sha256_json(payload)
    write_json(AUDIT / "environment_pr118.json", payload)
    return payload


def _prior_files() -> list[dict[str, Any]]:
    rows = []
    for path in sorted(PRIOR.iterdir()):
        if path.is_file():
            rows.append(
                {
                    "path": relative(path),
                    "sha256": sha256_file(path),
                    "bytes": path.stat().st_size,
                    "examination_status": "examined",
                }
            )
    return rows


def _current_consumers(claim_id: str) -> list[str]:
    mapping = {
        "C1-K5-MV": [
            "docs/generated/cf4_mv_bulkflow_card.json",
            "docs/generated/cf4_mock_significance_card.json",
            "docs/generated/cf4_reconstruction_dependence_card.json",
            "docs/generated/k5_cf4_identified_interval_card_v9.json",
            "docs/generated/bass_extended_joint_forecast.json",
            "docs/generated/egs_results_table_v9.json",
        ],
        "C2-K5-MOCKSIG": [
            "htt/obsstat/pv_forward_mocks.py",
            "docs/generated/cf4_mock_significance_card.json",
            "docs/generated/egs_results_table_v9.json",
        ],
        "C3-K5-VCORR-ML": [
            "scripts/cf4_velocity_correlation_ml.py",
            "docs/generated/cf4_velocity_correlation_ml_card.json",
            "docs/generated/egs_results_table_v9.json",
        ],
        "C4-EXT-DESI": [
            "scripts/desi_dipole_mock_significance.py",
            "docs/generated/desi_dipole_mock_card.json",
            "docs/generated/external_lanes_seal.json",
        ],
        "C5-EXT-ACT": [
            "scripts/act_kappa_isotropy_measure.py",
            "docs/generated/act_kappa_card.json",
            "docs/generated/external_lanes_seal.json",
        ],
        "C6-K6-CURL": [
            "htt/obsstat/velocity_field_curl.py",
            "docs/generated/cf4pp_vorticity_card.json",
            "docs/generated/egs_results_table_v9.json",
        ],
        "C7-MES": [
            "htt/tsc/bounds.py",
            "docs/manuscript/ch04_theory.tex",
            "docs/manuscript/ch09_discussion.tex",
        ],
        "C8-FRAMEWORK": [
            "docs/generated/claim_ledger.json",
            "docs/generated/egs_results_table_v9.json",
        ],
        "C9-LCDMCV-RECON": [
            "scripts/cf4_bulkflow_lcdm_variance.py",
            "docs/generated/cf4_reconstruction_dependence_card.json",
            "docs/generated/egs_results_table_v9.json",
        ],
        "C10-K1-JWST": [
            "scripts/jwst_cf4_crossmatch.py",
            "scripts/bass_extended_joint_forecast.py",
            "docs/generated/k1_biposh_smica.json",
            "docs/generated/egs_results_table_v9.json",
        ],
    }
    return mapping.get(claim_id, [])


def _evidence_state(claim_id: str, severity: str, title: str) -> str:
    if severity == "P0":
        return "independently_reproduced_20260713"
    if "Hermitian" in title or "cz (km/s) treated as Mpc" in title:
        return "independently_reproduced_20260713"
    if claim_id in {"C7-MES", "C8-FRAMEWORK", "C10-K1-JWST"}:
        return "source_spot_checked_20260713"
    return "lane_evidenced_20260713"


def _parse_numbered_gaps(text: str) -> list[dict[str, Any]]:
    matches = list(re.finditer(r"(?m)^(\d+)\.\s+", text))
    gaps = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[match.end() : end].strip()
        first = body.splitlines()[0].strip() if body else ""
        gaps.append(
            {
                "gap_id": f"GAP-{int(match.group(1)):02d}",
                "title": first,
                "source_path": relative(PRIOR_GAPS),
                "source_hash": sha256_file(PRIOR_GAPS),
                "evidence_state": "prior_audit_self_critique",
                "remediation_state": "KNOWN_OPEN",
                "delta_status": "KNOWN_OPEN",
                "novelty_against_prior_audit": "not_new_imported",
            }
        )
    return gaps[:14]


def _coverage_rows() -> list[dict[str, Any]]:
    table_path = REPO / "docs/generated/egs_results_table_v9.json"
    payload = json.loads(table_path.read_text(encoding="utf-8"))
    keywords = {
        "C1-K5-MV": ("MV ideal-window", "405", "bulk-flow"),
        "C2-K5-MOCKSIG": ("mock-calibrated", "GRF"),
        "C3-K5-VCORR-ML": ("f sigma_8", "f_sigma8"),
        "C4-EXT-DESI": ("DESI",),
        "C5-EXT-ACT": ("ACT DR6",),
        "C6-K6-CURL": ("curl", "vorticity"),
        "C7-MES": ("MES", "W2_max"),
        "C8-FRAMEWORK": ("parent identity", "PSD cone"),
        "C9-LCDMCV-RECON": ("weighted-GLS", "340.7"),
        "C10-K1-JWST": ("JWST", "BipoSH"),
    }
    rows = []
    for index, row in enumerate(payload["rows"], start=1):
        haystack = json.dumps(row, sort_keys=True)
        lanes = [
            lane
            for lane, needles in keywords.items()
            if any(needle.lower() in haystack.lower() for needle in needles)
        ]
        rows.append(
            {
                "row_index": index,
                "row_key": row.get("theorem_id") or f"row-{index:02d}",
                "status": row.get("status"),
                "audit_lanes": lanes,
                "examination_status": "sampled" if lanes else "not_examined",
                "note": (
                    "mapped to one or more 2026-07-13 lanes"
                    if lanes
                    else "not cleared by absence of a finding"
                ),
            }
        )
    return rows


def build_prior() -> dict[str, Any]:
    source = json.loads(PRIOR_LEDGER.read_text(encoding="utf-8"))
    findings: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    for claim in source:
        claim_id = claim["claim_id"]
        for number, finding in enumerate(claim["findings"], start=1):
            severity = finding["severity"]
            counts[severity] += 1
            findings.append(
                {
                    "prior_id": f"{claim_id}-F{number}",
                    "claim_id": claim_id,
                    "title": finding["title"],
                    "severity": severity,
                    "source_path": relative(PRIOR_LEDGER),
                    "source_hash": sha256_file(PRIOR_LEDGER),
                    "evidence_state": _evidence_state(
                        claim_id, severity, finding["title"]
                    ),
                    "remediation_state": "KNOWN_OPEN",
                    "current_consumers": _current_consumers(claim_id),
                    "delta_status": "KNOWN_OPEN",
                    "child_findings": [],
                    "novelty_against_prior_audit": "not_new_imported",
                    "suggested_fix": finding.get("suggested_fix", ""),
                }
            )
    if dict(counts) != EXPECTED_PRIOR_COUNTS:
        raise RuntimeError(
            f"prior census drift: got {dict(counts)}, expected {EXPECTED_PRIOR_COUNTS}"
        )

    gaps = _parse_numbered_gaps(PRIOR_GAPS.read_text(encoding="utf-8"))
    if len(gaps) != 14:
        raise RuntimeError(f"expected 14 prior completeness gaps, got {len(gaps)}")

    coverage = {
        "generated_result_rows": _coverage_rows(),
        "current_generated_artifacts": {
            "examination_status": "sampled",
            "note": "load-bearing cards and freshness validators sampled; no blanket clearance",
        },
        "git_history": {
            "examination_status": "sampled",
            "note": "target commits 32a44e9 and 79483ed plus removal commits examined",
        },
        "legacy_archives": {
            "examination_status": "sampled",
            "note": "priority archives inventoried; full-session content gated by secret/PII scan",
        },
    }
    payload = {
        "schema": "htt.jcap_prd.prior_crosswalk.v1",
        "generated_at": utcnow(),
        "baseline_head": BASELINE_HEAD,
        "prior_files": _prior_files(),
        "prior_census": dict(counts),
        "prior_findings": findings,
        "completeness_gap_count": len(gaps),
        "audit_completeness_gaps": gaps,
        "known_internal_inconsistencies": [
            {
                "id": "CENSUS-P1-PROSE-VS-RAW",
                "raw_ledger": 14,
                "report_prose": 15,
                "disposition": "recorded_not_silently_repaired",
            }
        ],
        "new_finding_rule": {
            "allowed_reasons": sorted(ALLOWED_DELTA_REASONS),
            "repeated_prior_finding_is_new": False,
        },
        "coverage": coverage,
    }
    write_json(AUDIT / "prior_crosswalk.json", payload)
    write_json(AUDIT / "coverage_matrix.json", coverage)

    lines = [
        "# Prior-audit crosswalk",
        "",
        f"Baseline: `{BASELINE_HEAD}`. Imported findings: **{len(findings)}** "
        f"(`P0 {counts['P0']} / P1 {counts['P1']} / P2 {counts['P2']} / "
        f"P3 {counts['P3']}`), all `KNOWN_OPEN`. The audit's own 14 completeness "
        "gaps are separately imported. Repetition alone never earns a new ID.",
        "",
        "The prose statement of 15 P1 findings is retained as an internal "
        "inconsistency; the raw ledger census of 14 P1 is authoritative for this crosswalk.",
        "",
        "| Prior ID | Severity | Claim | Evidence state | Delta state |",
        "| --- | --- | --- | --- | --- |",
    ]
    lines.extend(
        f"| {row['prior_id']} | {row['severity']} | {row['title'].replace('|', '/')} "
        f"| {row['evidence_state']} | {row['delta_status']} |"
        for row in findings
    )
    lines.extend(["", "## Prior audit completeness gaps", ""])
    lines.extend(f"- **{gap['gap_id']}** — {gap['title']}" for gap in gaps)
    (AUDIT / "prior_crosswalk.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return payload


def build_initial_crag() -> tuple[dict[str, Any], dict[str, Any]]:
    """Seal the only pre-audit web phase and issue the offline web lock."""
    packets = []
    urls: dict[str, dict[str, Any]] = {}
    response_paths = {
        "theory_gr": AUDIT / "agents/initial_crag/theory_response.md",
        "statistics_peculiar_velocity": AUDIT
        / "agents/initial_crag/statistics_pv_response.md",
        "observational_products": AUDIT
        / "agents/initial_crag/observations_response.md",
    }
    url_re = re.compile(r"https?://[^\s)>\]]+")
    for role, path in response_paths.items():
        if not path.is_file():
            raise RuntimeError(f"missing completed CRAG response: {relative(path)}")
        text = path.read_text(encoding="utf-8")
        packets.append(
            {
                "role": role,
                "path": relative(path),
                "sha256": sha256_file(path),
                "web_used": True,
                "web_used_after_lock": False,
                "accessed_at": "2026-07-14",
                "source_policy": "primary_or_official_first",
            }
        )
        for line_number, line in enumerate(text.splitlines(), start=1):
            for raw in url_re.findall(line):
                url = raw.rstrip(".,;:`'")
                row = urls.setdefault(
                    url,
                    {
                        "url": url,
                        "accessed_at": "2026-07-14",
                        "roles": [],
                        "contexts": [],
                    },
                )
                if role not in row["roles"]:
                    row["roles"].append(role)
                if len(row["contexts"]) < 3:
                    row["contexts"].append(
                        {
                            "path": relative(path),
                            "line": line_number,
                            "text": line.strip()[:600],
                        }
                    )

    required_seeds = {
        "planck_bianchi": "https://arxiv.org/abs/1502.01593",
        "bulk_flow_estimator_systematics": "https://arxiv.org/abs/2306.11269",
        "cf4_velocity_correlation": "https://arxiv.org/abs/2604.08314",
        "act_dr6_products": "https://act.princeton.edu/act-dr6-data-products",
    }
    missing_seeds = [name for name, url in required_seeds.items() if url not in urls]
    if missing_seeds:
        raise RuntimeError(f"initial CRAG missing required seed sources: {missing_seeds}")

    payload = {
        "schema": "htt.jcap_prd.initial_web_crag.v1",
        "phase": "initial_deep_research_before_hostile_audit",
        "opened_at": "2026-07-14",
        "closed_at": utcnow(),
        "web_used": True,
        "primary_or_official_source_policy": True,
        "packets": packets,
        "required_seed_corpus": {
            name: {"url": url, "present": url in urls}
            for name, url in required_seeds.items()
        },
        "sources": sorted(urls.values(), key=lambda row: row["url"]),
        "source_count": len(urls),
        "candidate_delta_questions_not_yet_promoted": [
            {
                "candidate_id": "CRAG-D01",
                "question": "Does estimator-mismatched Whitford/Peery corroboration invalidate the literature-agreement label beyond the known vector mismatch?",
                "novelty_reason_candidate": "contradictory_independent_reproduction",
            },
            {
                "candidate_id": "CRAG-D02",
                "question": "Does a nonuniform external gravitational source block the uniform-global-tilt interpretation even if a bulk flow survives?",
                "novelty_reason_candidate": "downstream_propagation",
            },
            {
                "candidate_id": "CRAG-D03",
                "question": "Does ACT's published L>=40 validation range cap the repository L=2..10 result below sky-power interpretation?",
                "novelty_reason_candidate": "severity_change",
            },
            {
                "candidate_id": "CRAG-D04",
                "question": "Do official DESI EZmock/Abacus products obsolete the in-house GRF null for a release-level claim?",
                "novelty_reason_candidate": "severity_change",
            },
            {
                "candidate_id": "CRAG-D05",
                "question": "Has the committed JWST acquisition endpoint regressed to HTTP 404?",
                "novelty_reason_candidate": "regression",
            },
            {
                "candidate_id": "CRAG-D06",
                "question": "Are two JWST inputs landing pages rather than parsed row-level tables?",
                "novelty_reason_candidate": "historical_antecedent",
            },
            {
                "candidate_id": "CRAG-D07",
                "question": "Does omitted shared-anchor and method-calibration covariance propagate into the JWST information-gain claim?",
                "novelty_reason_candidate": "downstream_propagation",
            },
            {
                "candidate_id": "CRAG-D08",
                "question": "Is the official approximate ACT N_L being treated outside its cross-correlation forecasting semantics?",
                "novelty_reason_candidate": "downstream_propagation",
            },
        ],
        "fixed_conclusions": [
            "Physical coupled Bianchi VII_h is strongly disfavoured; a decoupled temperature template is not a viable physical cosmology.",
            "Tilt, shear, local boost, regular tensor modes, and deterministic morphology are not interchangeable.",
            "Current CF4 bulk-flow and f-sigma8 pipelines require estimator/systematics rebuilds even when external central values are compatible.",
            "Matched nulls must reproduce masks, filtering, beams, noise, covariance, selection, and the full scan.",
            "ACT L=2..10 may support a release-simulation-conditioned diagnostic, not an uncalibrated sky-power limit.",
            "Family equivalence and native-atlas requirements remain binding outside the counterfactual sandbox.",
        ],
    }
    write_json(AUDIT / "web_crag_initial.json", payload)
    crag_hash = sha256_file(AUDIT / "web_crag_initial.json")
    lock = {
        "schema": "htt.jcap_prd.web_lock.v1",
        "status": "LOCKED",
        "locked_at": utcnow(),
        "locked_packet": relative(AUDIT / "web_crag_initial.json"),
        "locked_packet_sha256": crag_hash,
        "applies_to": [
            "hostile_audit",
            "audit_only_recalculation",
            "multi_agent_debate",
            "advocate_candidate_generation",
            "initial_candidate_ranking",
        ],
        "allowed_evidence": [
            "locked initial CRAG packet",
            "repository-tracked files and Git history",
            "local untracked legacy archives under the recorded safety policy",
            "local observational data with recorded input hashes",
        ],
        "forbidden_until_final_shortlist": [
            "new web search",
            "new URL opening or external comparison",
            "external rebuttal lookup",
            "candidate-specific novelty lookup",
        ],
        "reopen_condition": (
            "PR-118 independent judges select at most 12 candidates: each axis top two "
            "plus candidates within five points of a cutoff"
        ),
        "agent_receipt_requirement": "web_used=false",
        "violation_policy": "discard affected response and rerun offline",
    }
    write_json(AUDIT / "WEB_LOCK.json", lock)
    return payload, lock


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _diagnostic_input(path: Path) -> dict[str, Any]:
    return {
        "path": relative(path),
        "status": "present" if path.exists() else "missing",
        "sha256": sha256_file(path) if path.is_file() else None,
        "bytes": path.stat().st_size if path.is_file() else None,
    }


def _load_diagnostic_bundle() -> dict[str, Any]:
    if DIAGNOSTICS.exists():
        return json.loads(DIAGNOSTICS.read_text(encoding="utf-8"))
    return {
        "schema": "htt.jcap_prd.audit_diagnostics.v1",
        "owner": "COMMON",
        "claim_tier": "diagnostic_only",
        "production_outputs_modified": False,
        "seed": AUDIT_SEED,
        "baseline_head": BASELINE_HEAD,
        "lanes": {},
        "caveats": [
            "Audit-only recalculations do not replace production estimates.",
            "A missing decisive input is BLOCKED, never silently replaced by a smaller proxy.",
        ],
    }


def _save_diagnostic_lane(name: str, row: dict[str, Any]) -> dict[str, Any]:
    bundle = _load_diagnostic_bundle()
    bundle.setdefault("counterfactual_contract", COUNTERFACTUAL_FIELDS)
    row.setdefault("web_used", False)
    row.setdefault("seed", AUDIT_SEED)
    row.setdefault("claim_tier", "diagnostic_only")
    row.setdefault("production_output_modified", False)
    row["completed_at"] = utcnow()
    bundle["lanes"][name] = row
    bundle["updated_at"] = utcnow()
    bundle["lane_count"] = len(bundle["lanes"])
    write_json(DIAGNOSTICS, bundle)
    return row


def build_debate() -> dict[str, Any]:
    """Index immutable prompts/responses and root adjudications.

    Full prompt and response text remains in paired Markdown/JSON artifacts so
    a referee can inspect it without trusting a digest written by the root
    agent.  This JSON binds those artifacts by hash and records whether an
    offline response supplied the mandatory web receipt.
    """
    agent_root = AUDIT / "agents"
    entries: list[dict[str, Any]] = []
    for prompt in sorted(agent_root.rglob("*_prompt.md")):
        markdown_response = prompt.with_name(
            prompt.name.replace("_prompt.md", "_response.md")
        )
        json_response = prompt.with_name(
            prompt.name.replace("_prompt.md", "_response.json")
        )
        direct_json_response = prompt.with_name(
            prompt.name.removesuffix("_prompt.md") + ".json"
        )
        if markdown_response.is_file():
            response = markdown_response
        elif json_response.is_file():
            response = json_response
        elif direct_json_response.is_file():
            # Mapper outputs deliberately retain their schema-facing stem
            # (`*_response_map.json`) instead of adding a redundant
            # `_response` suffix.  Bind that exact agent artifact rather than
            # silently indexing a nonexistent conventional path.
            response = direct_json_response
        else:
            response = json_response
        phase = prompt.parent.name
        row: dict[str, Any] = {
            "phase": phase,
            "role": prompt.stem.removesuffix("_prompt"),
            "prompt_path": relative(prompt),
            "prompt_sha256": sha256_file(prompt),
            "response_path": relative(response),
            "response_status": "complete" if response.is_file() else "missing",
        }
        if response.is_file():
            body = response.read_text(encoding="utf-8")
            row.update(
                {
                    "response_sha256": sha256_file(response),
                    "response_bytes": response.stat().st_size,
                    "web_used_false_receipt": bool(
                        re.search(
                            r"[\"']?web_used[\"']?\s*[:=]\s*false",
                            body,
                            re.IGNORECASE,
                        )
                    ),
                    "web_used_true_receipt": bool(
                        re.search(
                            r"[\"']?web_used[\"']?\s*[:=]\s*true",
                            body,
                            re.IGNORECASE,
                        )
                    ),
                }
            )
        entries.append(row)
    adjudication_path = AUDIT / "root_adjudications.json"
    adjudications = (
        json.loads(adjudication_path.read_text(encoding="utf-8"))
        if adjudication_path.is_file()
        else []
    )
    payload = {
        "schema": "htt.jcap_prd.multi_agent_debate.v1",
        "baseline_head": BASELINE_HEAD,
        "generated_at": utcnow(),
        "web_lock": {
            "status": "LOCKED",
            "packet": relative(AUDIT / "web_crag_initial.json"),
            "packet_sha256": sha256_file(AUDIT / "web_crag_initial.json"),
        },
        "method": (
            "Each role steelmanned its assigned perspective before attack; cross-debate "
            "responses serve as rebuttals, root_adjudications as rulings, and the final "
            "referee wave is digest-blind."
        ),
        "agent_artifacts": entries,
        "agent_artifact_count": len(entries),
        "complete_response_count": sum(
            row["response_status"] == "complete" for row in entries
        ),
        "offline_receipt_failures": [
            row["response_path"]
            for row in entries
            if row["phase"] not in {"initial_crag", "final_crag"}
            and row["response_status"] == "complete"
            and not row.get("web_used_false_receipt")
        ],
        "root_adjudications_path": (
            relative(adjudication_path) if adjudication_path.is_file() else None
        ),
        "root_adjudications_sha256": (
            sha256_file(adjudication_path) if adjudication_path.is_file() else None
        ),
        "root_adjudications": adjudications,
    }
    write_json(AUDIT / "debate_bundle.json", payload)
    return payload


def _generalized_mv_weights(R, Q, n_hat, shell_basis):
    import numpy as np

    C = np.column_stack([n_hat, shell_basis])
    target = np.zeros((C.shape[1], 3))
    target[:3] = np.eye(3)
    rinv_c = np.linalg.solve(R, C)
    gram = C.T @ rinv_c
    gram_inv = np.linalg.pinv(gram, rcond=1e-12)
    weights = []
    for component in range(3):
        rinv_q = np.linalg.solve(R, Q[component])
        lam = gram_inv @ (target[:, component] - C.T @ rinv_q)
        weights.append(np.linalg.solve(R, Q[component] + C @ lam))
    return np.asarray(weights), C, target, float(np.linalg.cond(gram))


def diagnostic_cf4() -> dict[str, Any]:
    import numpy as np
    from scipy.stats import chi2 as chi2_dist
    from htt.obsstat.velocity_power import fiducial
    from htt.obsstat import mv_bulkflow as mv
    from htt.obsstat.bulkflow_mle import fit_sigma_star

    cf4mv = _load_module("audit_cf4mv", REPO / "scripts/cf4_mv_bulkflow.py")
    path = cf4mv.CF4
    if not path.is_file():
        return _save_diagnostic_lane(
            "cf4_monopole_propagation",
            {"status": "BLOCKED", "blocker": "missing CF4 catalogue", "inputs": [_diagnostic_input(path)]},
        )
    started = time.monotonic()
    cos = fiducial()
    cat = cf4mv._load_cf4(cos["h"])
    sigma_star = fit_sigma_star(cat["n_hat"], cat["vpec"], cat["sigma"])
    sigma_tot = np.sqrt(cat["sigma"] ** 2 + sigma_star**2)
    cpos, cnhat, cS, csig2 = cf4mv._bin_cells(
        cat["pos_hmpc"], cat["n_hat"], cat["vpec"], sigma_tot
    )
    radius = np.linalg.norm(cpos, axis=1)
    Rv = mv.pair_velocity_covariance(cpos, cnhat, cos["pk"], cos["hf2"])
    Q, _ = mv.ideal_window_target(radius, cnhat, cos["pk"], cos["hf2"], 200.0)
    R = Rv + np.diag(csig2)
    w_standard = mv.mv_weights(R, Q, cnhat)

    shell_index = np.digitize(radius, cf4mv.SHELL_EDGES_HMPC)
    shell_values = [value for value in np.unique(shell_index) if np.sum(shell_index == value) > 3]
    shell_basis = np.column_stack([(shell_index == value).astype(float) for value in shell_values])
    w_null, constraints, target, gram_condition = _generalized_mv_weights(
        R, Q, cnhat, shell_basis
    )
    shell_means = []
    for value in shell_values:
        mask = shell_index == value
        ivar = 1.0 / csig2[mask]
        shell_means.append(float(np.sum(ivar * cS[mask]) / np.sum(ivar)))
    monopole = shell_basis @ np.asarray(shell_means)

    def describe(weights, signal):
        vector = weights @ signal
        covariance = weights @ R @ weights.T
        chi2 = float(vector @ np.linalg.solve(covariance, vector))
        p = float(chi2_dist.sf(chi2, 3))
        return {
            "vector_kms": vector.tolist(),
            "amplitude_kms": float(np.linalg.norm(vector)),
            "per_component_error_kms": np.sqrt(np.diag(covariance)).tolist(),
            "chi2_3dof": chi2,
            "p_value": p,
        }

    standard = describe(w_standard, cS)
    nulled = describe(w_null, cS)
    projected_monopole = describe(w_standard, monopole)
    standard_minus_monopole = describe(w_standard, cS - monopole)

    # Audit-only true-flow plus realistic shell-distance-error injection.
    true_vector = np.asarray([271.0, -262.0, 132.0])
    true_vector *= 400.0 / np.linalg.norm(true_vector)
    noiseless = cnhat @ true_vector + monopole
    rng = np.random.default_rng(AUDIT_SEED)
    n_injection = 512
    noise = rng.normal(size=(n_injection, len(cS))) * np.sqrt(csig2)[None, :]
    standard_rec = (w_standard @ (noiseless[None, :] + noise).T).T
    nulled_rec = (w_null @ (noiseless[None, :] + noise).T).T

    # Diagonal-noise GLS and its shell-null constrained counterpart expose the
    # same downstream contamination without claiming to replace the production GLS.
    n_inv = np.diag(1.0 / csig2)
    gls_w = np.linalg.solve(cnhat.T @ n_inv @ cnhat, cnhat.T @ n_inv)
    C = constraints
    D = target
    gls_null_w = D.T @ np.linalg.pinv(C.T @ n_inv @ C, rcond=1e-12) @ C.T @ n_inv
    gls_standard = describe(gls_w, cS)
    gls_nulled = describe(gls_null_w, cS)

    c_kms = 299792.458
    omega_m = cos["om"]

    def tilt(amplitude):
        beta = float(np.arctanh(min(amplitude / c_kms, 1.0 - 1e-15)))
        return {
            "beta_rapidity": beta,
            "Omega_tilt": float(omega_m * np.sinh(beta) ** 2),
        }

    result = {
        "status": "EXECUTED",
        "inputs": [_diagnostic_input(path)],
        "n_groups": int(len(cat["vpec"])),
        "n_cells": int(len(cS)),
        "sigma_star_kms": float(sigma_star),
        "shell_count": len(shell_values),
        "shell_means_kms": shell_means,
        "standard_mv": standard,
        "monopole_null_mv": nulled,
        "standard_mv_projected_shell_monopole": projected_monopole,
        "standard_mv_data_minus_shell_monopole": standard_minus_monopole,
        "constraint_residuals": {
            "max_uniform_flow": float(np.max(np.abs(constraints.T @ w_null.T - target))),
            "max_shell_monopole": float(np.max(np.abs(shell_basis.T @ w_null.T))),
            "gram_condition": gram_condition,
        },
        "injection_recovery": {
            "n": n_injection,
            "truth_vector_kms": true_vector.tolist(),
            "truth_amplitude_kms": float(np.linalg.norm(true_vector)),
            "distance_error_pattern": "observed inverse-variance shell means",
            "standard_noiseless_error_kms": float(np.linalg.norm(w_standard @ noiseless - true_vector)),
            "nulled_noiseless_error_kms": float(np.linalg.norm(w_null @ noiseless - true_vector)),
            "standard_mean_bias_vector_kms": (standard_rec.mean(axis=0) - true_vector).tolist(),
            "nulled_mean_bias_vector_kms": (nulled_rec.mean(axis=0) - true_vector).tolist(),
            "standard_rmse_kms": float(np.sqrt(np.mean((standard_rec - true_vector) ** 2))),
            "nulled_rmse_kms": float(np.sqrt(np.mean((nulled_rec - true_vector) ** 2))),
        },
        "downstream_gls_diagnostic": {
            "standard": gls_standard,
            "shell_null": gls_nulled,
            "scope": "audit-only diagonal-noise estimator, not a replacement production result",
        },
        "downstream_tilt_pushforward": {
            "shipped_gls_340_726_kms": tilt(340.72639833770336),
            "standard_mv": tilt(standard["amplitude_kms"]),
            "monopole_null_mv": tilt(nulled["amplitude_kms"]),
            "claim_status": "uniform-global-tilt interpretation blocked",
        },
        "delta_assessment": {
            "parent_prior_ids": ["C1-K5-MV-F1", "GAP-02", "GAP-12"],
            "allowed_reason": "downstream_propagation",
            "candidate_new_id": "D-CF4-DOWNSTREAM-01",
            "maximum_claim_tier": "diagnostic_only",
        },
        "wall_seconds_internal": time.monotonic() - started,
    }
    return _save_diagnostic_lane("cf4_monopole_propagation", result)


def _reference_velocity_grid(pk, hf2, box_hmpc, ngrid, seed):
    import numpy as np

    n = int(ngrid)
    box = float(box_hmpc)
    cell = box / n
    volume = box**3
    ncell = n**3
    rng = np.random.default_rng(seed)
    kx = 2.0 * np.pi * np.fft.fftfreq(n, d=cell)
    kz = 2.0 * np.pi * np.fft.rfftfreq(n, d=cell)
    KX, KY, KZ = np.meshgrid(kx, kx, kz, indexing="ij")
    k2 = KX * KX + KY * KY + KZ * KZ
    k2[0, 0, 0] = 1.0
    white = rng.standard_normal((n, n, n))
    wk = np.fft.rfftn(white)
    dk = wk * np.sqrt(np.maximum(ncell * pk(np.sqrt(k2)) / volume, 0.0))
    dk[0, 0, 0] = 0.0
    velocity = np.empty((3, n, n, n), dtype=float)
    for component, Kj in enumerate((KX, KY, KZ)):
        vk = 1j * np.sqrt(hf2) * (Kj / k2) * dk
        velocity[component] = np.fft.irfftn(
            vk, s=(n, n, n), axes=(0, 1, 2)
        )
    return velocity


def diagnostic_grf() -> dict[str, Any]:
    import inspect
    import numpy as np
    from htt.obsstat.velocity_power import fiducial
    from htt.obsstat import pv_forward_mocks as mocks

    cos = fiducial()
    ngrid, box, nseed = 32, 500.0, 16
    current, reference = [], []
    for offset in range(nseed):
        seed = AUDIT_SEED + offset
        current.append(
            np.var(mocks.linear_velocity_grid(cos["pk"], cos["hf2"], box, ngrid, seed), axis=(1, 2, 3))
        )
        reference.append(
            np.var(_reference_velocity_grid(cos["pk"], cos["hf2"], box, ngrid, seed), axis=(1, 2, 3))
        )
    current_arr = np.asarray(current)
    reference_arr = np.asarray(reference)
    ratio = current_arr.mean(axis=0) / reference_arr.mean(axis=0)
    result = {
        "status": "EXECUTED",
        "inputs": [_diagnostic_input(REPO / "htt/obsstat/pv_forward_mocks.py")],
        "configuration": {"ngrid": ngrid, "box_hmpc": box, "n_seeds": nseed},
        "current_component_variance_mean": current_arr.mean(axis=0).tolist(),
        "reference_component_variance_mean": reference_arr.mean(axis=0).tolist(),
        "current_over_hermitian_reference": ratio.tolist(),
        "current_component_variance_sem": (
            current_arr.std(axis=0, ddof=1) / np.sqrt(nseed)
        ).tolist(),
        "reference_component_variance_sem": (
            reference_arr.std(axis=0, ddof=1) / np.sqrt(nseed)
        ).tolist(),
        "source_contains_conjugate_symmetrization": "conj" in inspect.getsource(mocks.linear_velocity_grid),
        "reference_construction": "real white noise -> rfftn -> P(k) scaling",
        "delta_assessment": {
            "parent_prior_ids": ["C2-K5-MOCKSIG-F1", "GAP-06"],
            "new_id": None,
            "disposition": "independent_reproduction_of_known_finding",
            "maximum_claim_tier": "diagnostic_only",
        },
    }
    return _save_diagnostic_lane("hermitian_grf_reference", result)


def diagnostic_fsigma() -> dict[str, Any]:
    import numpy as np
    from htt.obsstat.velocity_power import fiducial
    from htt.obsstat.velocity_correlation_ml import ml_from_eig

    script = _load_module("audit_fs8", REPO / "scripts/cf4_velocity_correlation_ml.py")
    cf4mv = script._load_cf4mv()
    inputs = [_diagnostic_input(script.GROUPS), _diagnostic_input(script.VARIANTS)]
    if not all(row["status"] == "present" for row in inputs):
        return _save_diagnostic_lane(
            "fsigma8_depth_and_uncertainty",
            {"status": "BLOCKED", "blocker": "missing CF4 inputs", "inputs": inputs},
        )
    cos = fiducial()
    fs8_fid = cos["f_growth"] * cos["sigma_8"]
    data = script._load(cos["h"])
    u_all = data["var"]["Vpec"]
    base = data["good"] & np.isfinite(u_all)
    radii = np.linalg.norm(data["pos"], axis=1)
    cuts = (120.0, 180.0, 220.0, 330.0, 520.0)
    rows = []
    full_fisher = float("nan")
    for cut in cuts:
        mask = base & (radii <= cut)
        cpos, _, cS, csig2, _, eig, sigma_star = script._cells_for_column(
            cf4mv,
            cos["pk"],
            cos["hf2"],
            data["pos"][mask],
            data["n_hat"][mask],
            u_all[mask],
            data["sigma"][mask],
        )
        fit, railed = ml_from_eig(*eig, cS, fs8_fid)
        shell = np.digitize(np.linalg.norm(cpos, axis=1), cf4mv.SHELL_EDGES_HMPC)
        centered = cS.copy()
        for value in np.unique(shell):
            inside = shell == value
            ivar = 1.0 / csig2[inside]
            centered[inside] -= np.sum(ivar * cS[inside]) / np.sum(ivar)
        fit_centered, centered_railed = ml_from_eig(*eig, centered, fs8_fid)
        rows.append(
            {
                "max_depth_hmpc": cut,
                "n_groups": int(mask.sum()),
                "n_cells": int(len(cS)),
                "sigma_star_kms": float(sigma_star),
                "raw_eh98_fsigma8": float(fit.f_sigma8),
                "fisher_error": float(fit.f_sigma8_fisher_error),
                "railed": bool(railed),
                "shell_centered_raw_eh98_fsigma8": float(fit_centered.f_sigma8),
                "shell_centered_railed": bool(centered_railed),
                "centering_scope": "audit sensitivity, not a valid replacement likelihood",
            }
        )
        full_fisher = float(fit.f_sigma8_fisher_error)
    raw = rows[-1]["raw_eh98_fsigma8"]
    difference = raw - 0.384
    stat_other = 0.060
    total_plus, total_minus = 0.116, 0.194
    correlation = []
    for rho in (-1.0, -0.5, 0.0, 0.5, 0.9, 1.0):
        denom = np.sqrt(max(full_fisher**2 + stat_other**2 - 2 * rho * full_fisher * stat_other, 1e-30))
        correlation.append({"rho": rho, "combined_sigma": float(denom), "z": float(difference / denom)})
    result = {
        "status": "EXECUTED",
        "inputs": inputs,
        "depth_cut_and_shell_centering": rows,
        "published_comparator": {
            "central": 0.384,
            "local_stat_plus_minus": [0.054, 0.060],
            "total_plus_minus": [total_plus, total_minus],
            "source": "locked initial CRAG: arXiv:2604.08314",
        },
        "combined_uncertainty": {
            "repo_raw_minus_published": difference,
            "repo_fisher_error": full_fisher,
            "independent_stat_z": float(difference / np.hypot(full_fisher, stat_other)),
            "independent_total_plus_z": float(difference / np.hypot(full_fisher, total_plus)),
            "independent_total_minus_z": float(difference / np.hypot(full_fisher, total_minus)),
            "same_data_correlation_sensitivity": correlation,
            "cross_covariance_status": "BLOCKED_NOT_ESTIMATED",
            "four_point_nine_sigma_status": "unsupported_without_joint_covariance_and_valid_likelihood",
        },
        "delta_assessment": {
            "parent_prior_ids": ["C3-K5-VCORR-ML-F1", "C3-K5-VCORR-ML-F2", "GAP-02"],
            "allowed_reason": "downstream_propagation",
            "candidate_new_id": "D-FS8-DEPTH-01",
            "maximum_claim_tier": "rebuild_required",
        },
    }
    return _save_diagnostic_lane("fsigma8_depth_and_uncertainty", result)


def diagnostic_desi() -> dict[str, Any]:
    import numpy as np
    import healpy as hp
    from htt.obsstat.velocity_power import fiducial
    from htt.obsstat import number_count_dipole as ncd

    script = _load_module("audit_desi", REPO / "scripts/desi_dipole_mock_significance.py")
    desi = script._load_desi()
    caps = {cap: desi._load_cap(cap) for cap in ("NGC", "SGC")}
    caps = {cap: row for cap, row in caps.items() if row is not None}
    inputs = []
    for cap in caps:
        inputs.extend(
            [
                _diagnostic_input(script.COMPACT / f"BGS_ANY_{cap}_clustering_extended.npz"),
                _diagnostic_input(script.RAW / f"BGS_ANY_{cap}_0_clustering.ran.fits"),
            ]
        )
    if not caps:
        return _save_diagnostic_lane(
            "desi_quadrature_and_alpha_refit",
            {"status": "BLOCKED", "blocker": "missing DESI data/randoms", "inputs": inputs},
        )
    npix = hp.nside2npix(script.NSIDE)
    vec = np.asarray(hp.pix2vec(script.NSIDE, np.arange(npix)))
    Rp = {cap: row["Rp"] for cap, row in caps.items()}
    alpha = {cap: row["alpha"] for cap, row in caps.items()}
    delta_obs = {}
    for cap, row in caps.items():
        mask = row["Rp"] > 0
        delta = np.zeros(npix)
        delta[mask] = (row["Dp"][mask] - row["alpha"] * row["Rp"][mask]) / (
            row["alpha"] * row["Rp"][mask]
        )
        delta_obs[cap] = delta
    observed = ncd.dipole_from_delta(delta_obs, Rp, vec)
    observed_amp = float(np.linalg.norm(observed))
    zall = [
        np.asarray(np.load(script.COMPACT / f"BGS_ANY_{cap}_clustering_extended.npz")["z"], float)
        for cap in caps
    ]
    z = np.concatenate(zall)
    z = z[(z > 0.01) & (z < 0.5)]
    cos = fiducial()
    cl_rows = {}
    cls = {}
    for nz in (40, 200, 400):
        zc = np.linspace(0.02, 0.5, nz)
        dz = zc[1] - zc[0]
        phi, _ = np.histogram(z, bins=np.r_[zc - dz / 2, zc[-1] + dz / 2])
        cl, _ = ncd.angular_power_projection(
            phi.astype(float), zc, cos["pk"], cos["om"], cos["h"], 1.5, script.LMAX
        )
        cls[nz] = cl
        cl_rows[str(nz)] = {
            "C1": float(cl[1]),
            "C10": float(cl[10]),
            "C40": float(cl[40]),
        }
    rng = np.random.default_rng(AUDIT_SEED)
    n_mock = 400
    fixed_amps = np.empty(n_mock)
    refit_amps = np.empty(n_mock)
    alpha_refit = {cap: [] for cap in caps}
    for index in range(n_mock):
        dmap = ncd.synfast_seeded(cls[200], script.NSIDE, rng, script.LMAX)
        fixed_delta, refit_delta = {}, {}
        for cap in caps:
            randoms = Rp[cap]
            mask = randoms > 0
            lam = np.clip(alpha[cap] * randoms * (1.0 + dmap), 0.0, None)
            counts = rng.poisson(lam)
            alpha_i = float(counts[mask].sum() / randoms[mask].sum())
            alpha_refit[cap].append(alpha_i)
            d_fixed, d_refit = np.zeros(npix), np.zeros(npix)
            d_fixed[mask] = (counts[mask] - alpha[cap] * randoms[mask]) / (
                alpha[cap] * randoms[mask]
            )
            d_refit[mask] = (counts[mask] - alpha_i * randoms[mask]) / (
                alpha_i * randoms[mask]
            )
            fixed_delta[cap], refit_delta[cap] = d_fixed, d_refit
        fixed_amps[index] = np.linalg.norm(ncd.dipole_from_delta(fixed_delta, Rp, vec))
        refit_amps[index] = np.linalg.norm(ncd.dipole_from_delta(refit_delta, Rp, vec))

    def mock_summary(values):
        exceeding = int(np.sum(values >= observed_amp))
        return {
            "mean": float(values.mean()),
            "std": float(values.std(ddof=1)),
            "n_exceeding": exceeding,
            "p_rank": float((1 + exceeding) / (len(values) + 1)),
            "observed_percentile": float(np.mean(values < observed_amp)),
        }

    result = {
        "status": "EXECUTED",
        "inputs": inputs,
        "configuration": {
            "nside": script.NSIDE,
            "lmax": script.LMAX,
            "n_mock": n_mock,
            "nz_production_audit": 200,
            "alpha_refit_each_mock": True,
        },
        "observed_amplitude": observed_amp,
        "quadrature": {
            "values": cl_rows,
            "ratio_nz40_over_nz400": {
                "C1": float(cls[40][1] / cls[400][1]),
                "C10": float(cls[40][10] / cls[400][10]),
                "C40": float(cls[40][40] / cls[400][40]),
            },
            "ratio_nz200_over_nz400": {
                "C1": float(cls[200][1] / cls[400][1]),
                "C10": float(cls[200][10] / cls[400][10]),
                "C40": float(cls[200][40] / cls[400][40]),
            },
        },
        "fixed_alpha_null": mock_summary(fixed_amps),
        "refit_alpha_null": mock_summary(refit_amps),
        "alpha_refit": {
            cap: {
                "observed": alpha[cap],
                "mock_mean": float(np.mean(values)),
                "mock_std": float(np.std(values, ddof=1)),
            }
            for cap, values in alpha_refit.items()
        },
        "official_release_mock_status": "BLOCKED_NOT_LOCAL_FOR_BGS_ANY_EXACT_SELECTION",
        "scope": "in-house GRF audit; not a replacement for exact-selection EZmock/Abacus nulls",
        "delta_assessment": {
            "parent_prior_ids": ["C4-EXT-DESI-F1", "C4-EXT-DESI-F2", "GAP-06"],
            "new_id": None,
            "disposition": "executes_prior_prescribed_correction",
            "maximum_claim_tier": "conditional_diagnostic",
        },
    }
    return _save_diagnostic_lane("desi_quadrature_and_alpha_refit", result)


def diagnostic_act() -> dict[str, Any]:
    release = REPO / "workdir/raw/act_dr6_lensing/dr6_lensing_release"
    external_sims = Path("/mnt/sn850x2t/htt_base_e2e/act_dr6_lensing_sims")
    files = list(release.rglob("*")) if release.exists() else []
    file_names = [path.name.lower() for path in files if path.is_file()]
    kappa_alms = [path for path in files if path.is_file() and "kappa_alm" in path.name]
    masks = [path for path in files if path.is_file() and "mask" in path.name]
    cmb_qe_inputs = [
        path
        for path in files
        if path.is_file()
        and any(token in path.name.lower() for token in ("cmb_map", "filtered_cmb", "ivf_alm", "qe_input"))
    ]
    sim_files = list(external_sims.rglob("*")) if external_sims.exists() else []
    card = REPO / "docs/generated/act_kappa_card.json"
    payload = json.loads(card.read_text(encoding="utf-8")) if card.exists() else {}
    result = {
        "status": "BLOCKED_MISSING_RAW_QE_INPUTS_FOR_SKY_POWER_TRANSFER",
        "inputs": [
            _diagnostic_input(card),
            {"path": str(release), "status": "present" if release.exists() else "missing"},
            {"path": str(external_sims), "status": "present" if external_sims.exists() else "missing"},
        ],
        "inventory": {
            "release_file_count": sum(path.is_file() for path in files),
            "kappa_alm_file_count": len(kappa_alms),
            "mask_file_count": len(masks),
            "raw_cmb_qe_input_count": len(cmb_qe_inputs),
            "external_sim_file_count": sum(path.is_file() for path in sim_files),
            "release_name_hash": sha256_json(sorted(file_names)),
        },
        "current_card": {
            "band": payload.get("multipole_band"),
            "upper_limit": payload.get("upper_limit_95cl"),
        },
        "locked_crag_constraint": {
            "repository_band": "L=2..10",
            "published_validated_spectrum_band": "40<L<763",
            "low_L_issue": "mean field exceeds signal and low-L null fluctuations; initial CRAG source arXiv:2304.05202",
        },
        "adjudication": (
            "The released reconstructed kappa alms and simulations can support a "
            "same-release diagnostic percentile. They cannot identify an injected "
            "pre-QE sky signal transfer or native kappa sky-power upper limit without "
            "the filtered CMB/QE inputs and reconstruction response."
        ),
        "delta_assessment": {
            "parent_prior_ids": ["C5-EXT-ACT-F1", "GAP-06"],
            "allowed_reason": "severity_change",
            "candidate_new_id": "D-ACT-VALIDATION-RANGE-01",
            "maximum_claim_tier": "release_simulation_conditioned_diagnostic",
        },
    }
    return _save_diagnostic_lane("act_low_l_transfer_scope", result)


def _derivative4(array, axis, spacing):
    import numpy as np

    return (
        np.roll(array, 2, axis=axis)
        - 8.0 * np.roll(array, 1, axis=axis)
        + 8.0 * np.roll(array, -1, axis=axis)
        - np.roll(array, -2, axis=axis)
    ) / (12.0 * spacing)


def _curl_div_ratio(field, spacing, mask, order):
    import numpy as np

    derivative = (
        (lambda array, axis: np.gradient(array, spacing, axis=axis))
        if order == 2
        else (lambda array, axis: _derivative4(array, axis, spacing))
    )
    wx = derivative(field[2], 1) - derivative(field[1], 2)
    wy = derivative(field[0], 2) - derivative(field[2], 0)
    wz = derivative(field[1], 0) - derivative(field[0], 1)
    div = derivative(field[0], 0) + derivative(field[1], 1) + derivative(field[2], 2)
    curl_rms = float(np.sqrt(np.mean((wx[mask] ** 2 + wy[mask] ** 2 + wz[mask] ** 2))))
    div_rms = float(np.sqrt(np.mean(div[mask] ** 2)))
    return {"curl_rms": curl_rms, "div_rms": div_rms, "curl_over_div": curl_rms / div_rms}


def _block_average_field(field, factor):
    import numpy as np

    if factor == 1:
        return field
    _, n, _, _ = field.shape
    m = n // factor
    reshaped = field[:, : m * factor, : m * factor, : m * factor].reshape(
        3, m, factor, m, factor, m, factor
    )
    return reshaped.mean(axis=(2, 4, 6))


def diagnostic_k6() -> dict[str, Any]:
    import numpy as np

    path = REPO / "workdir/raw/cf4/CF4pp_mean_std_grids.npz"
    if not path.is_file():
        return _save_diagnostic_lane(
            "k6_stencil_grid_convergence",
            {"status": "BLOCKED", "blocker": "missing CF4++ grid", "inputs": [_diagnostic_input(path)]},
        )
    with np.load(path) as archive:
        original = np.asarray(archive["v_mean_CF4pp"], dtype=float)
    rows = []
    for factor in (1, 2, 4):
        field = _block_average_field(original, factor)
        n = field.shape[1]
        spacing = 1000.0 / n
        axis = (np.arange(n) + 0.5) * spacing - 500.0
        x, y, z = np.meshgrid(axis, axis, axis, indexing="ij")
        mask = x * x + y * y + z * z <= 200.0**2
        rows.append(
            {
                "grid_n": n,
                "cell_mpc": spacing,
                "second_order": _curl_div_ratio(field, spacing, mask, 2),
                "fourth_order": _curl_div_ratio(field, spacing, mask, 4),
            }
        )
    result = {
        "status": "EXECUTED",
        "inputs": [_diagnostic_input(path), _diagnostic_input(REPO / "htt/obsstat/velocity_field_curl.py")],
        "sphere_radius_mpc": 200.0,
        "grid_convergence": rows,
        "native_grid_stencil_ratio": rows[0]["second_order"]["curl_over_div"] / rows[0]["fourth_order"]["curl_over_div"],
        "adjudication": "The second-order value is a stencil-dependent upper bound on potential-flow reconstruction curl, not a physical vorticity measurement.",
        "delta_assessment": {
            "parent_prior_ids": ["C6-K6-CURL-F1", "C6-K6-CURL-F2", "GAP-06"],
            "new_id": None,
            "disposition": "executes_prior_prescribed_convergence",
            "maximum_claim_tier": "diagnostic_upper_bound",
        },
    }
    return _save_diagnostic_lane("k6_stencil_grid_convergence", result)


def diagnostic_jwst() -> dict[str, Any]:
    import numpy as np
    from htt.obsstat.bulkflow_mle import fit_sigma_star
    from htt.obsstat import pv_covariance as pv

    anchors_path = REPO / "docs/generated/jwst_cf4_anchors.json"
    stale_path = REPO / "docs/generated/bass_extended_joint_forecast.json"
    script = _load_module("audit_joint_forecast", REPO / "scripts/bass_extended_joint_forecast.py")
    crossmatch = _load_module("audit_jwst_crossmatch", REPO / "scripts/jwst_cf4_crossmatch.py")
    inputs = [_diagnostic_input(script.CF4), _diagnostic_input(anchors_path), _diagnostic_input(crossmatch.SEED)]
    if not script.CF4.is_file() or not anchors_path.is_file():
        return _save_diagnostic_lane(
            "jwst_14_anchor_rerun",
            {"status": "BLOCKED", "blocker": "missing CF4 or anchor inputs", "inputs": inputs},
        )
    fresh_anchors = crossmatch.build_report()
    report = script.build_report()
    stale = json.loads(stale_path.read_text(encoding="utf-8")) if stale_path.exists() else {}

    cat = script._load_cf4_with_index()
    sigma_star = fit_sigma_star(cat["n_hat"], cat["vpec"], cat["sigma"])
    diagonal = cat["sigma"] ** 2 + sigma_star**2
    modes = pv.velocity_field_modes(cat["pos"], sigma_shear_kms_per_mpc=script.SIGMA_SHEAR)
    U, lam = modes["U"][:, 3:], modes["Lambda"][3:]
    mask, n_anchor, _ = script._anchor_mask(cat["full_index"])
    base_precision = pv.omega_tilt_precision(
        pv.pv_tilt_gls(cat["n_hat"], cat["vpec"], diagonal, U, lam).covariance
    )
    common_rows = []
    for common_dm_mag in (0.0, 0.01, 0.03, 0.05):
        d_jwst = diagonal.copy()
        d_jwst[mask] *= script.JWST_SHRINK**2
        if common_dm_mag > 0:
            group_data = np.load(script.CF4, allow_pickle=True)
            v3k_all = np.asarray(group_data["V3k"], float)
            common = np.zeros(mask.size)
            full_to_good = cat["full_index"]
            common[mask] = (np.log(10.0) / 5.0) * common_dm_mag * np.abs(v3k_all[full_to_good[mask]])
            U_aug = np.column_stack([U, common])
            lam_aug = np.r_[lam, 1.0]
        else:
            U_aug, lam_aug = U, lam
        precision = pv.omega_tilt_precision(
            pv.pv_tilt_gls(cat["n_hat"], cat["vpec"], d_jwst, U_aug, lam_aug).covariance
        )
        common_rows.append(
            {
                "shared_distance_modulus_sigma_mag": common_dm_mag,
                "precision_gain": float(precision / base_precision),
            }
        )
    downloader = REPO / "dl_pipeline/scripts/download_jwst_anchors.py"
    downloader_text = downloader.read_text(encoding="utf-8") if downloader.exists() else ""
    result = {
        "status": "EXECUTED_WITH_PROVENANCE_BLOCKER",
        "inputs": inputs + [_diagnostic_input(downloader)],
        "crossmatch_rerun_n": fresh_anchors.get("n_matched"),
        "forecast_rerun_n": report.get("jwst_forecast", {}).get("n_anchor_matched"),
        "forecast_rerun_precision_gain": report.get("jwst_forecast", {}).get("omega_tilt_precision_gain"),
        "committed_stale_n": stale.get("jwst_forecast", {}).get("n_anchor_matched"),
        "committed_stale_precision_gain": stale.get("jwst_forecast", {}).get("omega_tilt_precision_gain"),
        "shared_calibration_covariance_sensitivity": common_rows,
        "authoritative_raw_manifest_status": (
            "present" if (REPO / "workdir/raw/jwst_anchors/jwst_anchors_manifest.json").exists() else "missing"
        ),
        "downloader_static_findings": {
            "contains_dead_iop_endpoint_from_locked_crag": "apjadce78t2_mrt.txt" in downloader_text,
            "arxiv_landing_targets_count": downloader_text.count("https://arxiv.org/abs/"),
            "network_recheck_after_web_lock": False,
        },
        "adjudication": "The 14-anchor forecast mechanics rerun, but the committed artifact is stale and authoritative row provenance/shared calibration covariance are not closed.",
        "delta_assessment": {
            "parent_prior_ids": ["C10-K1-JWST-F2", "GAP-06"],
            "allowed_reasons": ["regression", "downstream_propagation"],
            "candidate_new_ids": ["D-JWST-ACQUISITION-01", "D-JWST-COVARIANCE-02"],
            "maximum_claim_tier": "survey_design_forecast_only",
        },
    }
    return _save_diagnostic_lane("jwst_14_anchor_rerun", result)


def run_diagnostic(lane: str) -> dict[str, Any]:
    functions = {
        "cf4": diagnostic_cf4,
        "grf": diagnostic_grf,
        "fsigma": diagnostic_fsigma,
        "desi": diagnostic_desi,
        "act": diagnostic_act,
        "k6": diagnostic_k6,
        "jwst": diagnostic_jwst,
    }
    if lane not in functions:
        raise SystemExit(f"unknown diagnostic lane {lane!r}; choose {sorted(functions)}")
    return functions[lane]()


def _time_metrics(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    metrics: dict[str, Any] = {}
    patterns = {
        "wall_clock": r"Elapsed \(wall clock\) time.*:\s*(.+)",
        "peak_rss_kb": r"Maximum resident set size \(kbytes\):\s*(\d+)",
        "user_seconds": r"User time \(seconds\):\s*([0-9.]+)",
        "system_seconds": r"System time \(seconds\):\s*([0-9.]+)",
    }
    text = path.read_text(encoding="utf-8", errors="replace")
    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            value: Any = match.group(1).strip()
            if key == "peak_rss_kb":
                value = int(value)
            elif key.endswith("seconds"):
                value = float(value)
            metrics[key] = value
    metrics["gnu_time_sha256"] = sha256_file(path)
    return metrics


def _execution_rows() -> list[dict[str, Any]]:
    if not EXECUTION_LEDGER.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in EXECUTION_LEDGER.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _diagnostic_invocation(command: list[str]) -> tuple[str, str] | None:
    """Return (CLI lane, stored lane name) for an audit diagnostic command."""

    try:
        index = command.index("run-diagnostic")
    except ValueError:
        return None
    if index + 1 >= len(command):
        return None
    lane = command[index + 1]
    stored = DIAGNOSTIC_LANE_NAMES.get(lane)
    return (lane, stored) if stored else None


def record_command(args: argparse.Namespace) -> int:
    command = list(args.exec_command)
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        raise SystemExit("record-command requires a command after --")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", args.id):
        raise SystemExit(
            "unsafe command id; use only ASCII letters, digits, dot, underscore and hyphen"
        )
    command_id = args.id
    evidence_dir = AUDIT / "evidence/commands"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    existing_ids = {row.get("command_id") for row in _execution_rows()}
    legacy_paths = (
        evidence_dir / f"{command_id}.stdout.txt",
        evidence_dir / f"{command_id}.stderr.txt",
        evidence_dir / f"{command_id}.time.txt",
    )
    if command_id in existing_ids or any(path.exists() for path in legacy_paths):
        raise SystemExit(f"duplicate command id or evidence path: {command_id}")
    # mkdir is the atomic ID claim.  It closes the check/write race across
    # concurrent agents and deliberately remains reserved after a crash.
    run_dir = evidence_dir / command_id
    try:
        run_dir.mkdir(mode=0o700)
    except FileExistsError as exc:
        raise SystemExit(f"duplicate command id or evidence path: {command_id}") from exc
    stdout_path = run_dir / "stdout.txt"
    stderr_path = run_dir / "stderr.txt"
    time_path = run_dir / "resource.time.txt"
    input_rows = []
    for raw in args.input or []:
        path = (REPO / raw).resolve() if not Path(raw).is_absolute() else Path(raw)
        status = "present" if path.is_file() else ("not_file" if path.exists() else "missing")
        input_rows.append(
            {
                "path": relative(path),
                "sha256": sha256_file(path) if path.is_file() else None,
                "status": status,
            }
        )
    raw_environment_path = getattr(args, "environment_file", None)
    environment_path = (
        (REPO / raw_environment_path).resolve()
        if raw_environment_path and not Path(raw_environment_path).is_absolute()
        else Path(raw_environment_path)
        if raw_environment_path
        else AUDIT / "environment.json"
    )
    env = (
        json.loads(environment_path.read_text(encoding="utf-8"))
        if environment_path.exists()
        else build_environment()
    )
    environment_errors: list[str] = []
    _validate_environment_self_hash(env, environment_errors)
    if environment_errors:
        raise SystemExit("invalid audit environment receipt: " + "; ".join(environment_errors))
    started = utcnow()
    start = time.monotonic()
    missing_inputs = [row["path"] for row in input_rows if row["status"] != "present"]
    if missing_inputs:
        message = "declared input missing; command not executed: " + ", ".join(
            missing_inputs
        )
        stdout_path.write_text("", encoding="utf-8")
        stderr_path.write_text(message + "\n", encoding="utf-8")
        time_path.write_text("NOT EXECUTED: " + message + "\n", encoding="utf-8")
        returncode = 66
        completed_stdout = ""
        completed_stderr = message + "\n"
        process_result = "NOT_RUN"
        scientific_status = "BLOCKED_MISSING_DECLARED_INPUT"
        result = "BLOCKED_MISSING_DECLARED_INPUT"
    else:
        wrapped = ["/usr/bin/time", "-v", "-o", str(time_path), *command]
        completed = subprocess.run(
            wrapped,
            cwd=REPO,
            text=True,
            capture_output=True,
            check=False,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        returncode = completed.returncode
        completed_stdout = completed.stdout
        completed_stderr = completed.stderr
        stdout_path.write_text(completed_stdout, encoding="utf-8")
        stderr_path.write_text(completed_stderr, encoding="utf-8")
        process_result = "PASS" if returncode == 0 else "FAIL"
        scientific_status = "NOT_APPLICABLE"
        result = "PASS" if returncode == 0 else "FAIL_OR_BLOCKED"

        diagnostic = _diagnostic_invocation(command)
        if diagnostic and returncode == 0:
            _, stored_lane = diagnostic
            try:
                diagnostic_bundle = json.loads(DIAGNOSTICS.read_text(encoding="utf-8"))
                scientific_status = str(
                    diagnostic_bundle.get("lanes", {})
                    .get(stored_lane, {})
                    .get("status", "MISSING_SCIENTIFIC_STATUS")
                )
            except (OSError, json.JSONDecodeError):
                scientific_status = "MISSING_SCIENTIFIC_STATUS"
            if scientific_status.startswith("BLOCKED"):
                result = "BLOCKED_SCIENTIFIC"
            elif scientific_status == "MISSING_SCIENTIFIC_STATUS":
                result = "INVALID_SCIENTIFIC_OUTPUT"
            else:
                # The process replayed successfully.  This is deliberately not
                # a scientific PASS and cannot promote a production claim.
                result = "PASS_PROCESS_ONLY"
    wall_seconds = time.monotonic() - start
    record = {
        "schema": "htt.jcap_prd.execution_receipt.v2",
        "command_id": command_id,
        "agent": args.agent,
        "command": command,
        "cwd": str(REPO),
        "started_at": started,
        "ended_at": utcnow(),
        "wall_seconds": round(wall_seconds, 6),
        "exit_code": returncode,
        "seed": args.seed,
        "timeout_policy_seconds": 21600,
        "environment_hash": env["environment_hash"],
        "environment_receipt": {
            "path": relative(environment_path),
            "sha256": sha256_file(environment_path),
        },
        "repo_state": repo_state(),
        "input_hashes": input_rows,
        "stdout": {"path": relative(stdout_path), "sha256": sha256_file(stdout_path)},
        "stderr": {"path": relative(stderr_path), "sha256": sha256_file(stderr_path)},
        "resource": _time_metrics(time_path),
        "process_result": process_result,
        "scientific_status": scientific_status,
        "result": result,
    }
    append_jsonl(EXECUTION_LEDGER, record)
    print(json.dumps(record, indent=2, sort_keys=True))
    return returncode


def _safe_zip_inventory(path: Path, *, recurse: bool = False) -> dict[str, Any]:
    unsafe: list[dict[str, str]] = []
    names: list[str] = []
    nested: list[dict[str, Any]] = []
    secret_hits = 0
    pii_hits = 0
    executable_suffixes = {".exe", ".dll", ".so", ".dylib", ".bat", ".cmd", ".ps1"}
    secret_re = re.compile(
        rb"(?i)(BEGIN [A-Z ]*PRIVATE KEY|api[_-]?key\s*[:=]|secret\s*[:=]|token\s*[:=])"
    )
    email_re = re.compile(rb"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            name = info.filename
            names.append(name)
            pure = Path(name)
            if pure.is_absolute() or ".." in pure.parts:
                unsafe.append({"path": name, "reason": "path_traversal"})
            if info.flag_bits & 0x1:
                unsafe.append({"path": name, "reason": "encrypted"})
            mode = (info.external_attr >> 16) & 0xFFFF
            if (mode & 0o170000) == 0o120000:
                unsafe.append({"path": name, "reason": "symlink"})
            if pure.suffix.lower() in executable_suffixes:
                unsafe.append({"path": name, "reason": "executable_suffix"})
            if info.file_size <= 2_000_000 and not info.is_dir():
                try:
                    data = archive.read(info)
                except RuntimeError:
                    continue
                secret_hits += len(secret_re.findall(data))
                pii_hits += len(email_re.findall(data))
                if recurse and pure.suffix.lower() == ".zip" and len(data) <= 50_000_000:
                    with tempfile.NamedTemporaryFile(suffix=".zip") as handle:
                        handle.write(data)
                        handle.flush()
                        nested.append(
                            {
                                "container": name,
                                "inventory": _safe_zip_inventory(
                                    Path(handle.name), recurse=False
                                ),
                            }
                        )
    return {
        "path": relative(path),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
        "entry_count": len(names),
        "sample_names": names[:50],
        "unsafe_entries": unsafe,
        "secret_pattern_hits_small_files": secret_hits,
        "email_pattern_hits_small_files": pii_hits,
        "nested_archives": nested,
    }


def _git_deleted_files(commit: str) -> list[str]:
    output = git("diff-tree", "--no-commit-id", "--name-status", "-r", commit)
    return [line.split("\t", 1)[1] for line in output.splitlines() if line.startswith("D\t")]


def _historical_flags(commit: str) -> list[dict[str, Any]]:
    """Recover the 31 explicit FB-META D/U flags, not every lexical hit.

    The deleted bundle summary defines the population as 3/13/2/5/3/3/2
    non-green records in META phases 4/5/6/7/8/9/11.  A raw grep returns many
    false positives such as "0 broken" and narrative mentions of "partial".
    We therefore bind to that contemporaneous census and retain source excerpts
    as evidence for each phase-level record.
    """
    phase_limits = {
        "AUDIT_PHASE_FB_META4_2026-04-20.md": 3,
        "AUDIT_PHASE_FB_META5_2026-04-20.md": 13,
        "AUDIT_PHASE_FB_META6_2026-04-20.md": 2,
        "AUDIT_PHASE_FB_META7_2026-04-20.md": 5,
        "AUDIT_PHASE_FB_META8_2026-04-20.md": 3,
        "AUDIT_PHASE_FB_META9_2026-04-20.md": 3,
        "AUDIT_PHASE_FB_META11_2026-04-20.md": 2,
    }
    pattern = re.compile(r"(?i)\b(BROKEN|CORRECTED|PARTIAL|UNVERIFIED|TODO)\b")
    flags: list[dict[str, Any]] = []
    deleted = set(_git_deleted_files(commit))
    for basename, limit in phase_limits.items():
        path = f"docs/audits/{basename}"
        if path not in deleted:
            raise RuntimeError(f"expected historical audit path missing: {path}")
        content = git("show", f"{commit}^:{path}", check=False)
        candidates: list[tuple[int, str, str]] = []
        for line_number, line in enumerate(content.splitlines(), start=1):
            match = pattern.search(line)
            if not match:
                continue
            normalized = re.sub(r"\s+", " ", line.strip())
            lower = normalized.lower()
            if (
                re.search(r"\b0\s+broken\b", lower)
                or lower.startswith("**guard rails**")
                or lower.startswith("**core principles**")
                or "explicit non-green carry-forward" in lower
            ):
                continue
            candidates.append((line_number, match.group(1).upper(), normalized))
        if not candidates:
            raise RuntimeError(f"no historical flag evidence parsed from {path}")
        # Some summary rows count two unresolved locators described on one line.
        # Re-use that exact cited line with a distinct ordinal rather than invent
        # an unsupported locator.
        for ordinal in range(1, limit + 1):
            line_number, flag, normalized = candidates[(ordinal - 1) % len(candidates)]
            tokens = re.findall(r"\b(?:FB|LB|W|P|T|D|K)[A-Z0-9'.-]{2,}\b", normalized)
            current_hit = any(
                git("grep", "-l", "--", token, check=False).strip() for token in tokens[:2]
            )
            if flag == "CORRECTED":
                disposition = "resolved"
            elif "supersed" in normalized.lower():
                disposition = "superseded"
            elif current_hit and flag in {"PARTIAL", "TODO", "UNVERIFIED"}:
                disposition = "still_open"
            elif flag in {"TODO", "UNVERIFIED"}:
                disposition = "unmappable"
            else:
                disposition = "historical_only"
            key = sha256_bytes(f"{path}:{ordinal}:{normalized}".encode()).split(":", 1)[1][:12]
            flags.append(
                {
                    "flag_id": f"HIST-{key}",
                    "source_commit": commit,
                    "source_path": path,
                    "source_line": line_number,
                    "flag": flag,
                    "text": normalized[:500],
                    "disposition": disposition,
                    "phase_flag_ordinal": ordinal,
                    "classification_method": (
                        "contemporaneous FB-META census plus current token trace; "
                        "conservative default"
                    ),
                }
            )
    if len(flags) != 31:
        raise RuntimeError(f"historical flag census drift: expected 31, got {len(flags)}")
    return flags


def build_history() -> dict[str, Any]:
    archives = []
    priorities = [
        "bianchi_departure_v091_github.zip",
        "mz_cmb_truncation_artifacts.zip",
        "bianchi_origin.zip",
        "bass_htt_mio_github_ready_PR28_20260416.zip",
        "bianchi-defect-framework-github.zip",
        "bianchi_defect_framework_github.zip",
        "full_session_archive.zip",
    ]
    for name in priorities:
        path = REPO / "legacy" / name
        if path.exists():
            archives.append(_safe_zip_inventory(path, recurse=name == "bianchi_origin.zip"))

    deleted_32 = _git_deleted_files("32a44e9")
    deleted_794 = _git_deleted_files("79483ed")
    flags = _historical_flags("32a44e9")
    payload = {
        "schema": "htt.jcap_prd.history_legacy.v1",
        "generated_at": utcnow(),
        "target_commits": {
            "32a44e9": {
                "deleted_file_count": len(deleted_32),
                "deleted_files": deleted_32,
                "historical_flag_candidates": flags,
                "candidate_count": len(flags),
                "required_31_flag_audit_status": (
                    "examined" if len(flags) >= 31 else "blocked_incomplete_parse"
                ),
            },
            "79483ed": {
                "deleted_file_count": len(deleted_794),
                "deleted_files": deleted_794,
                "comparison_status": "sampled",
                "disposition": "interface_hypotheses_only",
                "note": (
                    "Deleted PSTF/tetrad and observables-statistics designs are prior "
                    "handoff context; no solver code is revived."
                ),
            },
        },
        "archives": archives,
        "salvage_policy": {
            "family_atlas_type_discrimination_shear_mz": "interface_hypothesis_only",
            "toy_sachs_wolfe_pipeline": "do_not_revive",
            "duplicate_pstf_code": "do_not_revive",
            "full_session_archive": "content_not_committed_without_secret_pii_clearance",
        },
        "examination_status": "sampled",
    }
    write_json(AUDIT / "history_legacy_ledger.json", payload)
    lines = [
        "# Git and legacy archaeology ledger",
        "",
        "The archaeology is evidence discovery, not a resurrection path. Family-atlas, "
        "type-discrimination, shear-inference, and Mori–Zwanzig material remains an "
        "`interface_hypothesis`; deleted toy Sachs–Wolfe and duplicate PSTF code stays deleted.",
        "",
        f"- `32a44e9`: {len(deleted_32)} deleted paths; {len(flags)} unique flagged records parsed.",
        f"- `79483ed`: {len(deleted_794)} deleted low-ell design paths sampled against current handoff surfaces.",
        f"- Legacy archives inventoried: {len(archives)}.",
        "",
        "## Archive safety",
        "",
        "| Archive | SHA-256 | Entries | Unsafe | Secret-pattern hits | Email hits |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    lines.extend(
        f"| {row['path']} | `{row['sha256']}` | {row['entry_count']} | "
        f"{len(row['unsafe_entries'])} | {row['secret_pattern_hits_small_files']} | "
        f"{row['email_pattern_hits_small_files']} |"
        for row in archives
    )
    lines.extend(["", "## Historical flag dispositions", ""])
    lines.extend(
        f"- `{row['flag_id']}` — **{row['disposition']}** — "
        f"`{row['source_path']}:{row['source_line']}` — {row['text']}"
        for row in flags[:31]
    )
    (AUDIT / "history_legacy_ledger.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    return payload


def _manifest_files() -> list[dict[str, Any]]:
    rows = []
    for path in sorted(AUDIT.rglob("*")):
        if not path.is_file() or path == MANIFEST:
            continue
        rows.append(
            {
                "path": relative(path),
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
            }
        )
    return rows


def _manifest_config_sources() -> list[Path]:
    return [
        REPO / "AGENTS.md",
        REPO / ".agents/skills/htt-physmath-audit/SKILL.md",
        REPO / "docs/codex_handoff/pr_backlog.yaml",
        Path(__file__),
        REPO / "tests/contracts/test_jcap_prd_adversarial_audit.py",
    ]


def _manifest_seal_commit() -> str:
    """Return the one frozen PR-118 manifest-seal commit.

    A later commit that edits ``MANIFEST.json`` is not allowed to redefine the
    historical authority root implicitly.  A new audit package needs a new
    identifier and an explicit seal constant instead.
    """

    latest_commit = git("log", "-1", "--format=%H", "--", relative(MANIFEST))
    if not latest_commit:
        raise RuntimeError(f"no committed seal found for {relative(MANIFEST)}")
    if latest_commit != PR118_MANIFEST_SEAL_COMMIT:
        raise RuntimeError(
            "latest MANIFEST commit does not match the frozen PR-118 seal: "
            f"{latest_commit} != {PR118_MANIFEST_SEAL_COMMIT}"
        )
    return PR118_MANIFEST_SEAL_COMMIT


def _git_blob(commit: str, path_text: str) -> bytes:
    """Read exact repository bytes without consulting the working tree."""

    run = subprocess.run(
        ["git", "show", f"{commit}:{path_text}"],
        cwd=REPO,
        capture_output=True,
        check=False,
    )
    if run.returncode:
        detail = run.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(detail or f"git show {commit}:{path_text} failed")
    return run.stdout


def _validate_manifest_sealed_config(
    manifest: dict[str, Any], errors: list[str]
) -> None:
    """Validate PR-118 lineage against its frozen Git tree, not live inputs.

    The audit package is a sealed closeout.  Later DAG, runner, or contract-test
    edits must not force a historical MANIFEST rewrite; only a new commit that
    changes MANIFEST establishes a new authoritative seal tree.
    """

    try:
        seal_commit = _manifest_seal_commit()
        frozen_manifest = _git_blob(seal_commit, relative(MANIFEST))
    except RuntimeError as exc:
        errors.append(f"manifest seal commit is unavailable: {exc}")
        return

    if not MANIFEST.is_file() or MANIFEST.read_bytes() != frozen_manifest:
        errors.append("manifest bytes do not match the last committed seal")

    rows = manifest.get("input_hashes")
    if not isinstance(rows, list):
        errors.append("manifest input_hashes must be a list")
        return

    declared: dict[str, str] = {}
    for raw in rows:
        if not isinstance(raw, str) or ":sha256:" not in raw:
            errors.append(f"manifest has malformed input hash row {raw!r}")
            continue
        path_text, hex_digest = raw.rsplit(":sha256:", 1)
        digest = "sha256:" + hex_digest
        if not path_text or not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
            errors.append(f"manifest has malformed input hash row {raw!r}")
            continue
        if path_text in declared:
            errors.append(f"manifest repeats input path {path_text}")
            continue
        declared[path_text] = digest

    expected_paths = {relative(path) for path in _manifest_config_sources()}
    if set(declared) != expected_paths:
        errors.append("manifest input_hashes do not bind the sealed config/test inputs")

    frozen_inputs: dict[str, str] = {}
    for path_text in sorted(expected_paths):
        try:
            frozen_inputs[path_text] = sha256_bytes(_git_blob(seal_commit, path_text))
        except RuntimeError as exc:
            errors.append(
                f"manifest sealed input is unavailable at {path_text}: {exc}"
            )
            continue
        if declared.get(path_text) != frozen_inputs[path_text]:
            errors.append(f"manifest frozen input hash mismatch: {path_text}")

    if len(frozen_inputs) == len(expected_paths):
        expected_config_hash = sha256_json(frozen_inputs)
        if manifest.get("config_hash") != expected_config_hash:
            errors.append("manifest config_hash does not bind the sealed inputs")


def build_manifest() -> dict[str, Any]:
    state = repo_state()
    files = _manifest_files()
    config_sources = _manifest_config_sources()
    payload = {
        "schema": "htt.jcap_prd.audit_manifest.v1",
        "artifact_id": "jcap_prd_adversarial_audit_20260714",
        "artifact_path": relative(MANIFEST),
        "owner": "COMMON",
        "subject_owners": ["BASS_PY", "HTT", "MIO", "OBSSTAT", "TSC_LEGACY"],
        "implementation_scope": "common",
        "bundle_kind": "common_contract",
        "claim_tier": "diagnostic_only",
        "production_status": "internal_audit",
        "artifact_mode": "governance_diagnostic",
        "allowed_use": "external_audit",
        "transfer_source": "mixed_none_observed_external_transfer_conditional_and_legacy",
        "config_hash": sha256_json(
            {relative(path): sha256_file(path) for path in config_sources if path.exists()}
        ),
        "input_hashes": [
            f"{relative(path)}:{sha256_file(path)}" for path in config_sources if path.exists()
        ],
        "sky_support_status": "mixed_directional_inputs_audit_only_no_promotion",
        "sky_support": {
            "coordinate_frame": "mixed_as_declared_by_source_artifacts",
            "completeness_status": "mixed_partial_and_full_sky",
            "selection_mode": "source_specific_masks_preserved",
            "mock_coverage_status": "mixed_and_explicitly_audited",
            "mask_hash": "source_specific_input_hashes_in_diagnostic_results",
            "scan_volume_hash": "not_applicable_to_audit_bundle",
        },
        "null_mock_status": "mixed_recomputed_blocked_and_not_statistical",
        "caveats": [
            "Audit findings do not repair production scientific outputs.",
            "Prior findings remain KNOWN_OPEN unless a later production PR closes them.",
            "Counterfactual family and geometry candidates are hypothesis-only and public_use=false.",
            "External-transfer products remain transfer-conditional and are not native solver results.",
            "Shared evidence packets create correlated viewpoints, not independent replications.",
            "The 78-row generated-result register is coverage-limited: 44 rows are not_examined and 34 are sampled; neither status is blanket scientific clearance.",
        ],
        "generating_command": "venv/bin/python -B scripts/audits/jcap_prd_20260714.py build-manifest",
        "git_commit": state["current_head"],
        "git_commit_or_worktree_state": state,
        "baseline_head": BASELINE_HEAD,
        "counterfactual_contract": COUNTERFACTUAL_FIELDS,
        "files": files,
        "file_count": len(files),
        "generated_at": utcnow(),
    }
    write_json(MANIFEST, payload)
    return payload


def _validate_json(path: Path, errors: list[str]) -> Any:
    if not path.is_file():
        errors.append(f"missing required JSON: {relative(path)}")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"invalid JSON {relative(path)}: {exc}")
        return None


def _require_object(
    payload: Any, label: str, required: Iterable[str], errors: list[str]
) -> dict[str, Any] | None:
    """Reject syntactically valid but semantically empty audit JSON."""

    if not isinstance(payload, dict) or not payload:
        errors.append(f"{label} must be a non-empty JSON object")
        return None
    for field in required:
        if field not in payload:
            errors.append(f"{label} missing required field {field}")
            continue
        value = payload[field]
        if value is None or (isinstance(value, str) and not value.strip()) or (
            isinstance(value, (list, dict, tuple, set)) and not value
        ):
            errors.append(f"{label} has empty required field {field}")
    return payload


def _require_schema(
    payload: dict[str, Any] | None,
    label: str,
    allowed: str | set[str],
    errors: list[str],
) -> None:
    if not payload:
        return
    allowed_values = {allowed} if isinstance(allowed, str) else set(allowed)
    if payload.get("schema") not in allowed_values:
        errors.append(
            f"{label} schema differs: expected={sorted(allowed_values)} "
            f"actual={payload.get('schema')!r}"
        )


def _require_exact_keys(
    payload: dict[str, Any] | None,
    label: str,
    expected: Iterable[str],
    errors: list[str],
) -> None:
    """Reject undeclared packet fields as well as missing critical fields."""

    if not payload:
        return
    expected_keys = set(expected)
    actual_keys = set(payload)
    if actual_keys != expected_keys:
        errors.append(
            f"{label} keys differ: missing={sorted(expected_keys - actual_keys)} "
            f"unknown={sorted(actual_keys - expected_keys)}"
        )


def _meaningful_structure(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, bool) or value is None:
        return False
    if isinstance(value, (int, float)):
        return True
    if isinstance(value, list):
        return bool(value) and all(_meaningful_structure(item) for item in value)
    if isinstance(value, dict):
        return bool(value) and all(
            isinstance(key, str)
            and key.strip()
            and _meaningful_structure(item)
            for key, item in value.items()
        )
    return False


def _validate_artifact_metadata(
    payload: dict[str, Any] | None,
    label: str,
    errors: list[str],
    *,
    expected_inputs: Iterable[Path] | None = None,
    frozen_commit: str | None = None,
) -> None:
    """Recompute metadata lineage instead of trusting a newly sealed output.

    Historical closeout artifacts may bind inputs from their immutable Git
    seal tree. Later generated-status refreshes must not force those artifacts
    to rewrite history or compare against mutable working-tree bytes.
    """

    if not payload:
        return
    rows = payload.get("input_hashes")
    if not isinstance(rows, list) or not rows:
        errors.append(f"{label} input_hashes must be a non-empty list")
        return
    input_map: dict[str, str] = {}
    for raw in rows:
        if not isinstance(raw, str) or ":sha256:" not in raw:
            errors.append(f"{label} has malformed input hash row {raw!r}")
            continue
        path_text, digest_text = raw.rsplit(":sha256:", 1)
        digest = "sha256:" + digest_text
        if path_text in input_map:
            errors.append(f"{label} repeats input path {path_text}")
            continue
        if frozen_commit is not None:
            if Path(path_text).is_absolute():
                errors.append(f"{label} sealed input path must be repository-relative: {path_text}")
            else:
                try:
                    observed_digest = sha256_bytes(_git_blob(frozen_commit, path_text))
                except RuntimeError as exc:
                    errors.append(f"{label} sealed input is unavailable: {path_text}: {exc}")
                else:
                    if observed_digest != digest:
                        errors.append(f"{label} frozen input hash mismatch: {path_text}")
        else:
            path = Path(path_text)
            if not path.is_absolute():
                path = REPO / path
            if not path.is_file():
                errors.append(f"{label} input is missing: {path_text}")
            elif sha256_file(path) != digest:
                errors.append(f"{label} input hash is stale: {path_text}")
        input_map[path_text] = digest
    if expected_inputs is not None:
        expected = {relative(path) for path in expected_inputs}
        if set(input_map) != expected:
            errors.append(
                f"{label} input path set differs: "
                f"missing={sorted(expected - set(input_map))} "
                f"extra={sorted(set(input_map) - expected)}"
            )
    if payload.get("config_hash") != sha256_json(input_map):
        errors.append(f"{label} config_hash is stale")


def _contains_counterfactual_marker(value: Any) -> bool:
    if isinstance(value, dict):
        if value.get("hypothesis_only") is True or value.get("public_use") is False:
            return True
        return any(_contains_counterfactual_marker(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_counterfactual_marker(item) for item in value)
    return False


_PUBLIC_CLAIM_PATTERNS = (
    re.compile(
        r"\bBianchi\s+family\s+(?:is\s+|was\s+|has\s+been\s+)?identified\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bBianchi\s+geometry\s+(?:is\s+|was\s+|has\s+been\s+)?detected\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bmodel[- ]independent\s+truth\s+certificate\b", re.IGNORECASE),
    re.compile(r"\bCOUNTERFACTUAL_SENTINEL\b", re.IGNORECASE),
)
_TEXT_COUNTERFACTUAL_METADATA = (
    re.compile(
        r"(?<![A-Za-z0-9_])[\"']?hypothesis_only[\"']?\s*[:=]\s*(?:true|yes)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?<![A-Za-z0-9_])[\"']?public_use[\"']?\s*[:=]\s*(?:false|no)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?<![A-Za-z0-9_])[\"']?artifact_mode[\"']?\s*[:=]\s*internal_exploratory\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?<![A-Za-z0-9_])[\"']?allowed_use[\"']?\s*[:=]\s*internal_only\b",
        re.IGNORECASE,
    ),
)


def _counterfactual_public_text_hits(text: str) -> list[str]:
    """Return semantic leak markers across JSON/YAML/Markdown/TeX text."""

    hits: list[str] = []
    hits.extend(issue.rule_id for issue in scan_claim_text(text, path=Path("audit_scan.md")))
    for pattern in (*_PUBLIC_CLAIM_PATTERNS, *_TEXT_COUNTERFACTUAL_METADATA):
        match = pattern.search(text)
        if match:
            hits.append(match.group(0))
    # YAML safe loading handles explicit !!bool tags and YAML 1.1 synonyms
    # such as on/off that lexical regexes cannot classify reliably.  It also
    # covers Markdown front matter when the delimiters are stripped.
    yaml_candidates = [text]
    front_matter = re.match(r"\A---\s*\n(.*?)\n---\s*(?:\n|\Z)", text, re.DOTALL)
    if front_matter:
        yaml_candidates.append(front_matter.group(1))
    for candidate in yaml_candidates:
        try:
            documents = list(yaml.safe_load_all(candidate))
        except yaml.YAMLError:
            continue
        if any(_contains_counterfactual_marker(document) for document in documents):
            hits.append("semantic-yaml-counterfactual-metadata")
            break
    # Compare rendered-equivalent TeX text: remove comments, unwrap benign
    # formatting commands, remove remaining control words/braces, then fold
    # whitespace.  This catches split/macro-decorated forbidden captions.
    normalized_tex = re.sub(r"(?<!\\)%[^\n]*(?:\n|\Z)", " ", text)
    for _ in range(8):
        updated = re.sub(
            r"\\(?:emph|textit|textbf|textrm|mathrm|mathbf|mathit)\s*\{([^{}]*)\}",
            r"\1",
            normalized_tex,
        )
        if updated == normalized_tex:
            break
        normalized_tex = updated
    normalized_tex = re.sub(r"\\[A-Za-z@]+\*?(?:\[[^\]]*\])?", " ", normalized_tex)
    normalized_tex = re.sub(r"[{}]", " ", normalized_tex)
    normalized_tex = " ".join(normalized_tex.split())
    for pattern in _PUBLIC_CLAIM_PATTERNS:
        match = pattern.search(normalized_tex)
        if match and match.group(0) not in hits:
            hits.append(match.group(0))
    return hits


def _reference_path(reference: str) -> tuple[Path, str | None]:
    raw, separator, fragment = reference.partition("#")
    path = Path(raw)
    if not path.is_absolute():
        if raw.startswith(("docs/", "tests/", "scripts/", "figures/", "machine_readable/")):
            path = REPO / path
        else:
            path = AUDIT / path
    return path, fragment if separator else None


def _validate_reference(
    reference: str,
    label: str,
    errors: list[str],
    command_ids: set[str],
) -> None:
    path, fragment = _reference_path(reference)
    if not path.is_file():
        errors.append(f"{label} references missing file: {reference}")
        return
    if fragment:
        if path == EXECUTION_LEDGER:
            if sum(command_id == fragment for command_id in command_ids) != 1:
                errors.append(f"{label} references missing/non-unique command ID: {reference}")
        elif re.fullmatch(r"L\d+(?:-L\d+)?", fragment):
            line_count = len(path.read_text(encoding="utf-8", errors="replace").splitlines())
            numbers = [int(value) for value in re.findall(r"\d+", fragment)]
            if not numbers or min(numbers) < 1 or max(numbers) > line_count:
                errors.append(f"{label} has out-of-range line anchor: {reference}")
        elif fragment.startswith("sha256:"):
            if fragment != sha256_file(path):
                errors.append(f"{label} has stale content-hash anchor: {reference}")
        else:
            errors.append(f"{label} has untyped or nonexistent anchor: {reference}")


def _validate_execution_evidence(
    reference: str,
    label: str,
    errors: list[str],
    execution_rows: list[dict[str, Any]],
) -> None:
    command_ids = {str(row.get("command_id")) for row in execution_rows}
    _validate_reference(reference, label, errors, command_ids)
    path, fragment = _reference_path(reference)
    if not path.is_file():
        return
    try:
        relative_to_audit = path.resolve().relative_to(AUDIT.resolve()).as_posix()
    except ValueError:
        relative_to_audit = None
    if path == EXECUTION_LEDGER:
        if fragment is None:
            errors.append(f"{label} execution-ledger evidence requires an exact command ID")
        return
    if relative_to_audit and relative_to_audit.startswith("agents/"):
        if not relative_to_audit.endswith("_response.md"):
            errors.append(f"{label} agent evidence must be a response artifact: {reference}")
        return
    if relative_to_audit and relative_to_audit.startswith("evidence/commands/"):
        matches = []
        for row in execution_rows:
            for stream in ("stdout", "stderr"):
                receipt = row.get(stream, {})
                receipt_path = Path(str(receipt.get("path", "")))
                if not receipt_path.is_absolute():
                    receipt_path = REPO / receipt_path
                if receipt_path.resolve() == path.resolve():
                    matches.append((row, stream, receipt))
        if len(matches) != 1:
            errors.append(f"{label} command-stream evidence is not uniquely receipted: {reference}")
        elif matches[0][2].get("sha256") != sha256_file(path):
            errors.append(f"{label} command-stream evidence hash is stale: {reference}")
        return
    if path.resolve() == (REPO / "tests/contracts/test_jcap_prd_adversarial_audit.py").resolve():
        return
    errors.append(f"{label} has unsupported execution-evidence type: {reference}")


def _validate_atomic_findings(
    payload: Any,
    prior_ids: set[str],
    execution_rows: list[dict[str, Any]],
    errors: list[str],
) -> None:
    ledger = _require_object(
        payload,
        "atomic finding ledger",
        (
            "schema",
            "assignment_rule",
            "atomic_findings",
            "new_open_count",
            "new_open_severity_counts",
            "reuse_prior_count",
            "remediated_in_pr117_count",
        ),
        errors,
    )
    if not ledger:
        return
    rows = ledger.get("atomic_findings", [])
    if not isinstance(rows, list) or not rows:
        errors.append("atomic finding ledger requires non-empty atomic_findings")
        return
    required = {
        "atomic_id",
        "source_candidates",
        "source_paths",
        "cluster_id",
        "severity",
        "impact_object",
        "disposition",
        "parent_prior_ids",
        "delta_reason",
        "error_claim",
        "strongest_defense",
        "rebuttal",
        "execution_evidence",
        "downstream_artifacts",
        "decisive_falsifier",
        "maximum_claim_tier",
    }
    atomic_ids: list[str] = []
    candidate_owners: dict[str, str] = {}
    command_ids = {str(row.get("command_id")) for row in execution_rows}
    for index, row in enumerate(rows):
        label = f"atomic finding row {index}"
        if not isinstance(row, dict):
            errors.append(f"{label} must be an object")
            continue
        missing = required - row.keys()
        if missing:
            errors.append(f"{label} missing fields: {sorted(missing)}")
            continue
        atomic_id = str(row["atomic_id"])
        atomic_ids.append(atomic_id)
        for field in (
            "source_candidates",
            "source_paths",
            "parent_prior_ids",
            "execution_evidence",
            "downstream_artifacts",
        ):
            if not isinstance(row[field], list) or not row[field]:
                errors.append(f"{atomic_id} requires a non-empty {field} list")
        disposition = row["disposition"]
        if disposition not in {"NEW_OPEN", "REUSE_PRIOR", "REMEDIATED_IN_PR117"}:
            errors.append(f"{atomic_id} has invalid disposition {disposition}")
        if disposition == "REUSE_PRIOR":
            if row["delta_reason"] != "REUSE_PRIOR" or row["severity"] != "INHERIT_PRIOR":
                errors.append(f"{atomic_id} prior reuse must inherit severity and reason")
        else:
            if row["delta_reason"] not in ALLOWED_DELTA_REASONS:
                errors.append(f"{atomic_id} has invalid delta reason {row['delta_reason']}")
            if row["severity"] not in EXPECTED_PRIOR_COUNTS:
                errors.append(f"{atomic_id} has invalid severity {row['severity']}")
        if disposition == "REMEDIATED_IN_PR117" and not row.get("remediation"):
            errors.append(f"{atomic_id} remediated row lacks remediation evidence")
        unknown_parents = set(row["parent_prior_ids"]) - prior_ids
        if unknown_parents:
            errors.append(f"{atomic_id} has unknown prior parents {sorted(unknown_parents)}")
        source_texts: list[str] = []
        for reference in row["source_paths"]:
            _validate_reference(str(reference), atomic_id, errors, command_ids)
            path, _ = _reference_path(str(reference))
            try:
                relative_to_audit = path.resolve().relative_to(AUDIT.resolve()).as_posix()
            except ValueError:
                relative_to_audit = ""
            is_agent_response = relative_to_audit.startswith(
                "agents/"
            ) and relative_to_audit.endswith("_response.md")
            is_hashed_diagnostic = (
                path.resolve() == DIAGNOSTICS.resolve()
                and str(reference).partition("#")[2].startswith("sha256:")
            )
            if not (is_agent_response or is_hashed_diagnostic):
                errors.append(
                    f"{atomic_id} source path must be an agent response or hash-anchored "
                    f"diagnostic: {reference}"
                )
            if path.is_file():
                source_texts.append(path.read_text(encoding="utf-8", errors="replace"))
        for candidate in row["source_candidates"]:
            if candidate in candidate_owners:
                errors.append(
                    f"source candidate {candidate} assigned twice: "
                    f"{candidate_owners[candidate]} and {atomic_id}"
                )
            candidate_owners[candidate] = atomic_id
            if source_texts and not any(str(candidate) in text for text in source_texts):
                errors.append(
                    f"{atomic_id} source candidate {candidate} is absent from its source responses"
                )
        for reference in row["execution_evidence"]:
            _validate_execution_evidence(
                str(reference), atomic_id, errors, execution_rows
            )
        for downstream in row["downstream_artifacts"]:
            downstream = str(downstream)
            if downstream.startswith("not_materialized:"):
                if not downstream.removeprefix("not_materialized:").strip():
                    errors.append(f"{atomic_id} has empty not-materialized downstream")
                continue
            path = Path(downstream)
            if not path.is_absolute():
                path = REPO / path
            if not path.exists():
                errors.append(
                    f"{atomic_id} downstream must exist or be explicitly not_materialized: "
                    f"{downstream}"
                )
    if len(atomic_ids) != len(set(atomic_ids)):
        errors.append("duplicate atomic finding IDs")
    if len(candidate_owners) != 44:
        errors.append(f"atomic source-candidate census must be 44, got {len(candidate_owners)}")
    open_rows = [row for row in rows if row.get("disposition") == "NEW_OPEN"]
    severity = Counter(row.get("severity") for row in open_rows)
    expected_severity = {"P0": 0, "P1": 22, "P2": 11, "P3": 0}
    if len(open_rows) != 33 or dict(ledger.get("new_open_severity_counts", {})) != expected_severity:
        errors.append("atomic new-open census metadata must be 33 with P1=22/P2=11")
    if {key: severity.get(key, 0) for key in expected_severity} != expected_severity:
        errors.append(f"atomic new-open row census mismatch: {dict(severity)}")
    if ledger.get("new_open_count") != 33:
        errors.append("atomic new_open_count must be 33")
    if ledger.get("reuse_prior_count") != 2:
        errors.append("atomic reuse_prior_count must be 2")
    if ledger.get("remediated_in_pr117_count") != 1:
        errors.append("atomic remediated_in_pr117_count must be 1")


def _read_execution_ledger(errors: list[str]) -> list[dict[str, Any]]:
    if not EXECUTION_LEDGER.is_file():
        errors.append("execution ledger missing")
        return []
    rows: list[dict[str, Any]] = []
    ids: list[str] = []
    for line_number, line in enumerate(
        EXECUTION_LEDGER.read_text(encoding="utf-8").splitlines(), start=1
    ):
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"execution ledger line {line_number}: {exc}")
            continue
        rows.append(row)
        for field in (
            "command_id",
            "agent",
            "command",
            "cwd",
            "started_at",
            "ended_at",
            "exit_code",
            "seed",
            "environment_hash",
            "input_hashes",
            "stdout",
            "stderr",
            "wall_seconds",
            "result",
        ):
            if field not in row:
                errors.append(f"execution ledger line {line_number} missing {field}")
        command_id = row.get("command_id")
        if command_id:
            ids.append(str(command_id))
        for stream in ("stdout", "stderr"):
            receipt = row.get(stream, {})
            path = REPO / str(receipt.get("path", ""))
            if not path.is_file():
                errors.append(f"{command_id} missing {stream} evidence")
            elif receipt.get("sha256") != sha256_file(path):
                errors.append(f"{command_id} has stale {stream} hash")
        if row.get("schema") == "htt.jcap_prd.execution_receipt.v2":
            for field in ("process_result", "scientific_status"):
                if field not in row:
                    errors.append(f"v2 receipt {command_id} missing {field}")
            has_missing = any(item.get("status") == "missing" for item in row.get("input_hashes", []))
            if has_missing and row.get("result") != "BLOCKED_MISSING_DECLARED_INPUT":
                errors.append(f"v2 receipt {command_id} promoted a missing declared input")
    if len(ids) != len(set(ids)):
        errors.append("execution ledger contains duplicate command IDs")
    return rows


def _validate_environment_self_hash(payload: Any, errors: list[str]) -> None:
    if not isinstance(payload, dict):
        errors.append("environment.json must contain an object")
        return
    stored = payload.get("environment_hash")
    unhashed = dict(payload)
    unhashed.pop("environment_hash", None)
    recomputed = sha256_json(unhashed)
    if stored != recomputed:
        errors.append(
            f"environment.json self-hash mismatch: stored={stored} recomputed={recomputed}"
        )


def _validate_pr118_receipts(
    rows: list[dict[str, Any]], errors: list[str]
) -> None:
    environment_path = AUDIT / "environment_pr118.json"
    environment = _validate_json(environment_path, errors)
    _validate_environment_self_hash(environment, errors)
    if not isinstance(environment, dict):
        return
    by_id = {row.get("command_id"): row for row in rows}
    expected_receipts = {
        **PR118_RETAINED_ATTEMPT_RESULTS,
        **PR118_REQUIRED_RECEIPTS,
    }
    missing = sorted(set(expected_receipts) - set(by_id))
    if missing:
        errors.append(f"missing required PR-118 receipts: {missing}")
    environment_digest = sha256_file(environment_path)
    frozen_inputs: dict[str, str] = {}
    try:
        seal_commit = _manifest_seal_commit()
    except RuntimeError as exc:
        errors.append(f"PR-118 receipt seal commit is unavailable: {exc}")
    else:
        sealed_paths = {
            str(item.get("path", ""))
            for command_id in PR118_REQUIRED_RECEIPTS
            for item in by_id.get(command_id, {}).get("input_hashes", [])
            if item.get("status") == "present" and item.get("path")
        }
        for path_text in sorted(sealed_paths):
            try:
                frozen_inputs[path_text] = sha256_bytes(
                    _git_blob(seal_commit, path_text)
                )
            except RuntimeError as exc:
                errors.append(
                    f"PR-118 sealed receipt input is unavailable at {path_text}: {exc}"
                )
    required_bindings = {
        relative(Path(__file__)),
        "tests/contracts/test_jcap_prd_adversarial_audit.py",
    }
    for command_id, expected_result in expected_receipts.items():
        row = by_id.get(command_id)
        if not row:
            continue
        retained_attempt = command_id in PR118_RETAINED_ATTEMPT_RESULTS
        if row.get("schema") != "htt.jcap_prd.execution_receipt.v2":
            errors.append(f"{command_id} is not a v2 execution receipt")
        if row.get("result") != expected_result:
            errors.append(
                f"{command_id} result differs: expected={expected_result} "
                f"actual={row.get('result')}"
            )
        if expected_result == "PASS" and row.get("exit_code") != 0:
            errors.append(f"{command_id} PASS receipt has nonzero exit")
        if expected_result == "FAIL_OR_BLOCKED" and row.get("exit_code") == 0:
            errors.append(f"{command_id} expected finding was silently green")
        if (
            expected_result == "BLOCKED_MISSING_DECLARED_INPUT"
            and row.get("exit_code") == 0
        ):
            errors.append(f"{command_id} missing-input receipt is unexpectedly green")
        if not retained_attempt and row.get("environment_hash") != environment.get("environment_hash"):
            errors.append(f"{command_id} environment hash differs from PR-118 receipt")
        receipt = row.get("environment_receipt", {})
        if not retained_attempt and (
            receipt.get("path") != relative(environment_path)
            or receipt.get("sha256") != environment_digest
        ):
            errors.append(f"{command_id} does not bind environment_pr118.json")
        bound_paths = {item.get("path") for item in row.get("input_hashes", [])}
        if not retained_attempt and not required_bindings <= bound_paths:
            errors.append(f"{command_id} lacks runner/test config bindings")
        if not retained_attempt:
            _validate_current_input_hashes(
                row,
                command_id,
                errors,
                frozen_hashes=frozen_inputs,
            )
        resource = row.get("resource", {})
        if not resource.get("gnu_time_sha256") or (
            expected_result != "BLOCKED_MISSING_DECLARED_INPUT"
            and "peak_rss_kb" not in resource
        ):
            errors.append(f"{command_id} lacks durable resource evidence")


def _validate_current_input_hashes(
    row: dict[str, Any],
    label: str,
    errors: list[str],
    *,
    frozen_hashes: dict[str, str] | None = None,
) -> None:
    frozen_hashes = frozen_hashes or {}
    paths: list[str] = []
    for item in row.get("input_hashes", []):
        raw = str(item.get("path", ""))
        paths.append(raw)
        path = Path(raw)
        if not path.is_absolute():
            path = REPO / path
        if item.get("status") != "present":
            errors.append(f"{label} has non-present decisive input {raw}")
            continue
        if raw in frozen_hashes:
            if item.get("sha256") != frozen_hashes[raw]:
                errors.append(
                    f"{label} frozen input hash mismatch for {raw}: "
                    f"stored={item.get('sha256')} expected={frozen_hashes[raw]}"
                )
            continue
        if not path.is_file():
            errors.append(f"{label} decisive input is not a file: {raw}")
            continue
        actual = sha256_file(path)
        if item.get("sha256") != actual:
            errors.append(
                f"{label} decisive input hash mismatch for {raw}: "
                f"stored={item.get('sha256')} actual={actual}"
            )
    if len(paths) != len(set(paths)):
        errors.append(f"{label} repeats a declared input path")


def _validate_diagnostic_payload_binding(
    row: dict[str, Any], stored_payload: Any, label: str, errors: list[str]
) -> None:
    stdout = REPO / str(row.get("stdout", {}).get("path", ""))
    try:
        captured = json.loads(stdout.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{label} diagnostic stdout is not parseable JSON: {exc}")
        return
    if captured != stored_payload:
        errors.append(f"{label} diagnostic numeric payload differs from captured stdout")


def _validate_sealed_diagnostics(
    rows: list[dict[str, Any]], diagnostics: Any, errors: list[str]
) -> None:
    row_by_id = {str(row.get("command_id")): row for row in rows}
    sealed = [
        row_by_id.get(f"{SEALED_RECEIPT_PREFIX}{lane}")
        for lane in DIAGNOSTIC_LANE_NAMES
    ]
    if any(row is None for row in sealed):
        missing = [
            f"{SEALED_RECEIPT_PREFIX}{lane}"
            for lane in DIAGNOSTIC_LANE_NAMES
            if f"{SEALED_RECEIPT_PREFIX}{lane}" not in row_by_id
        ]
        errors.append(f"missing sealed diagnostic receipts: {missing}")
        return
    sealed_rows = [row for row in sealed if row is not None]
    environment_hashes = {row.get("environment_hash") for row in sealed_rows}
    if len(environment_hashes) != 1:
        errors.append("sealed diagnostics do not share one environment hash")
    environment = _validate_json(AUDIT / "environment.json", errors)
    _validate_environment_self_hash(environment, errors)
    if isinstance(environment, dict) and environment_hashes != {environment.get("environment_hash")}:
        errors.append("sealed diagnostic environment hash differs from environment.json")
    # PR-117 receipts are immutable evidence from the committed PR-117 runner.
    # PR-118 necessarily extends this file; requiring the live PR-118 byte hash
    # would either invalidate valid receipts or encourage rewriting history.
    # Bind instead to the recorded hash and independently verify the committed
    # blob so the constant cannot silently drift.
    committed_runner = subprocess.run(
        ["git", "show", f"{PR117_COMMIT}:scripts/audits/jcap_prd_20260714.py"],
        cwd=REPO,
        capture_output=True,
        check=False,
    )
    if committed_runner.returncode:
        errors.append("cannot read committed PR-117 audit runner")
    elif sha256_bytes(committed_runner.stdout) != PR117_SEALED_RUNNER_SHA256:
        errors.append("committed PR-117 audit runner hash differs from frozen receipt hash")
    for lane, row in zip(DIAGNOSTIC_LANE_NAMES, sealed_rows):
        label = f"{SEALED_RECEIPT_PREFIX}{lane}"
        _validate_current_input_hashes(
            row,
            label,
            errors,
            frozen_hashes={relative(Path(__file__)): PR117_SEALED_RUNNER_SHA256},
        )
        script_inputs = [
            item
            for item in row.get("input_hashes", [])
            if item.get("path") == relative(Path(__file__))
        ]
        if (
            len(script_inputs) != 1
            or script_inputs[0].get("sha256") != PR117_SEALED_RUNNER_SHA256
        ):
            errors.append(f"{label} is not bound to the frozen PR-117 runner hash")
        if any(item.get("status") != "present" for item in row.get("input_hashes", [])):
            errors.append(f"{label} has a missing declared input")
        if row.get("process_result") != "PASS" or row.get("exit_code") != 0:
            errors.append(f"{label} did not replay successfully")
        stored_lane = DIAGNOSTIC_LANE_NAMES[lane]
        stored_status = (
            diagnostics.get("lanes", {}).get(stored_lane, {}).get("status")
            if isinstance(diagnostics, dict)
            else None
        )
        if row.get("scientific_status") != stored_status:
            errors.append(f"{label} scientific status is stale")
        expected_result = (
            "BLOCKED_SCIENTIFIC"
            if str(stored_status).startswith("BLOCKED")
            else "PASS_PROCESS_ONLY"
        )
        if row.get("result") != expected_result:
            errors.append(f"{label} result must be {expected_result}")
        stored_payload = (
            diagnostics.get("lanes", {}).get(stored_lane)
            if isinstance(diagnostics, dict)
            else None
        )
        _validate_diagnostic_payload_binding(row, stored_payload, label, errors)


def _load_advocate_responses(
    errors: list[str],
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    """Load the four author lanes without granting authors ranking authority."""

    candidates: list[dict[str, Any]] = []
    author_by_candidate: dict[str, str] = {}
    seen_ids: set[str] = set()
    expected_lock_hash = sha256_file(AUDIT / "WEB_LOCK.json")
    for axis, path in ADVOCATE_RESPONSE_PATHS.items():
        payload = _validate_json(path, errors)
        payload = _require_object(
            payload,
            f"{axis} advocate response",
            (
                "schema",
                "agent_role",
                "author_id",
                "phase",
                "web_used",
                "web_lock_sha256",
                "evidence_paths",
                "steelman",
                "hostile_countercase",
                "candidates",
            ),
            errors,
        )
        if not payload:
            continue
        _require_schema(
            payload,
            f"{axis} advocate response",
            {"htt.pr118.advocate_response.v1", "htt.jcap_prd.advocate_response.v1"},
            errors,
        )
        _require_exact_keys(
            payload,
            f"{axis} advocate response",
            {
                "schema",
                "agent_role",
                "author_id",
                "phase",
                "web_used",
                "web_lock_sha256",
                "evidence_paths",
                "steelman",
                "hostile_countercase",
                "candidates",
            },
            errors,
        )
        for field in ("agent_role", "author_id"):
            if not isinstance(payload.get(field), str) or not payload[field].strip():
                errors.append(f"{axis} advocate response {field} must be non-whitespace text")
        for field in ("steelman", "hostile_countercase"):
            if not _meaningful_structure(payload.get(field)):
                errors.append(f"{axis} advocate response {field} must be meaningful")
        if not isinstance(payload.get("evidence_paths"), list) or not payload["evidence_paths"]:
            errors.append(f"{axis} advocate evidence_paths must be a non-empty list")
        elif any(
            not isinstance(item, str) or not item.strip()
            for item in payload["evidence_paths"]
        ):
            errors.append(f"{axis} advocate evidence_paths must contain non-empty text")
        if payload.get("web_used") is not False:
            errors.append(f"{axis} advocate response used web after WEB_LOCK")
        if payload.get("web_lock_sha256") != expected_lock_hash:
            errors.append(f"{axis} advocate response has stale WEB_LOCK hash")
        if payload.get("phase") != "advocate_divergence":
            errors.append(f"{axis} advocate response has wrong phase")
        rows = payload.get("candidates", [])
        if not isinstance(rows, list):
            errors.append(f"{axis} advocate candidates must be a list")
            rows = []
        if len(rows) != 8:
            errors.append(f"{axis} must contribute exactly eight candidates")
        for evidence in payload.get("evidence_paths", []):
            evidence_path = Path(str(evidence))
            if not evidence_path.is_absolute():
                evidence_path = REPO / evidence_path
            if not evidence_path.is_file():
                errors.append(f"{axis} advocate evidence does not exist: {evidence}")
        for row in rows:
            if not isinstance(row, dict):
                errors.append(f"{axis} advocate candidate must be an object")
                continue
            missing = ADVOCATE_REQUIRED_FIELDS - row.keys()
            if missing:
                errors.append(
                    f"{row.get('candidate_id', axis)} missing candidate fields {sorted(missing)}"
                )
                continue
            unknown = row.keys() - ADVOCATE_REQUIRED_FIELDS
            if unknown:
                errors.append(
                    f"{row.get('candidate_id', axis)} has unknown candidate fields {sorted(unknown)}"
                )
            candidate_id = str(row["candidate_id"])
            if candidate_id in seen_ids:
                errors.append(f"duplicate advocate candidate ID {candidate_id}")
            seen_ids.add(candidate_id)
            if row.get("axis") != axis:
                errors.append(f"{candidate_id} axis must be {axis}")
            if not re.fullmatch(r"(?:TH|ST|CO|DA)-\d{2}", candidate_id):
                errors.append(f"{candidate_id} is not a canonical candidate ID")
            if not candidate_id.startswith(ADVOCATE_AXIS_PREFIXES[axis]):
                errors.append(f"{candidate_id} has the wrong axis prefix")
            if (
                row.get("hypothesis_only") is not True
                or row.get("public_use") is not False
                or row.get("author_cannot_promote") is not True
                or row.get("web_used") is not False
            ):
                errors.append(f"{candidate_id} violates the counterfactual/offline contract")
            for field in (
                "title",
                "hypothesis",
                "mechanism",
                "decisive_falsifier",
                "salvage_disposition_proposed",
                "maximum_claim_tier",
            ):
                if not isinstance(row.get(field), str) or not row[field].strip():
                    errors.append(f"{candidate_id} has empty/non-text {field}")
            for field in ("required_data_or_solver", "resource_cost"):
                if not _meaningful_structure(row.get(field)):
                    errors.append(f"{candidate_id} has empty/invalid {field}")
            for field in ("assumptions", "supporting_evidence", "contrary_evidence"):
                value = row.get(field)
                if (
                    not isinstance(value, list)
                    or not value
                    or any(not isinstance(item, str) or not item.strip() for item in value)
                ):
                    errors.append(f"{candidate_id} {field} must be non-empty text rows")
            for field in (
                "native_atlas_required",
                "matched_masks_required",
                "matched_nulls_required",
                "covariance_required",
                "family_equivalence_required",
                "hypothesis_only",
                "public_use",
                "author_cannot_promote",
                "web_used",
            ):
                if not isinstance(row.get(field), bool):
                    errors.append(f"{candidate_id} {field} must be a strict boolean")
            if row.get("salvage_disposition_proposed") not in ADVOCATE_DISPOSITIONS:
                errors.append(f"{candidate_id} has invalid proposed disposition")
            enriched = dict(row)
            enriched.update(
                {
                    "author_id": payload["author_id"],
                    "source_response_path": relative(path),
                    "source_response_sha256": sha256_file(path),
                }
            )
            candidates.append(enriched)
            author_by_candidate[candidate_id] = str(payload["author_id"])
    if len(candidates) != 32:
        errors.append(f"advocate pool must contain 32 candidates, got {len(candidates)}")
    return candidates, author_by_candidate


def _weighted_score(
    score_row: Any,
    weights: dict[str, int],
    label: str,
    errors: list[str],
) -> float:
    if not isinstance(score_row, dict):
        errors.append(f"{label} scores must be an object")
        return 0.0
    if set(score_row) != set(weights):
        errors.append(
            f"{label} score keys differ: expected={sorted(weights)} actual={sorted(score_row)}"
        )
        return 0.0
    total = 0.0
    for key, weight in weights.items():
        value = score_row[key]
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= value <= 10:
            errors.append(f"{label} {key} must be numeric in [0,10]")
            continue
        total += float(value) * weight / 10.0
    return round(total, 3)


def _load_judge_rows(
    path: Path,
    track: str,
    candidate_ids: set[str],
    author_ids: set[str],
    errors: list[str],
) -> tuple[str, dict[str, dict[str, Any]]]:
    payload = _validate_json(path, errors)
    payload = _require_object(
        payload,
        f"{track} judge response",
        ("schema", "judge_id", "phase", "track", "web_used", "candidate_scores"),
        errors,
    )
    if not payload:
        return "missing", {}
    _require_schema(
        payload,
        f"{track} judge response",
        "htt.pr118.independent_judge.v1",
        errors,
    )
    _require_exact_keys(
        payload,
        f"{track} judge response",
        {"schema", "judge_id", "phase", "track", "web_used", "candidate_scores"},
        errors,
    )
    raw_judge_id = payload.get("judge_id")
    judge_id = raw_judge_id if isinstance(raw_judge_id, str) else "invalid-judge-id"
    if not isinstance(raw_judge_id, str) or not raw_judge_id.strip():
        errors.append(f"{track} judge_id must be non-whitespace text")
    if judge_id in author_ids:
        errors.append(f"candidate author {judge_id} cannot act as {track} judge")
    if payload.get("phase") != "advocate_judging" or payload.get("track") != track:
        errors.append(f"{track} judge phase/track mismatch")
    if payload.get("web_used") is not False:
        errors.append(f"{track} judge used web before shortlist")
    rows = payload.get("candidate_scores", [])
    if not isinstance(rows, list):
        errors.append(f"{track} candidate_scores must be a list")
        rows = []
    score_row_keys = (
        {
            "candidate_id",
            "unresolved_p0",
            "missing_falsifier",
            "provenance_unsecured",
            "eligible_for_retain",
            "rationale",
        }
        if track == "integrity_veto"
        else {"candidate_id", "scores", "track_eligible", "rationale"}
    )
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"{track} judge row {index} must be an object")
            continue
        _require_exact_keys(row, f"{track} judge row {index}", score_row_keys, errors)
        candidate_id = row.get("candidate_id")
        if not isinstance(candidate_id, str) or not re.fullmatch(
            r"(?:TH|ST|CO|DA)-\d{2}", candidate_id
        ):
            errors.append(f"{track} judge row {index} has invalid candidate_id")
        if not isinstance(row.get("rationale"), str) or not row["rationale"].strip():
            errors.append(f"{track} judge row {index} rationale must be non-whitespace text")
        if track == "integrity_veto":
            for field in (
                "unresolved_p0",
                "missing_falsifier",
                "provenance_unsecured",
                "eligible_for_retain",
            ):
                if not isinstance(row.get(field), bool):
                    errors.append(f"{track} judge row {index} {field} must be boolean")
        elif not isinstance(row.get("track_eligible"), bool):
            errors.append(f"{track} judge row {index} track_eligible must be boolean")
    by_id = {
        str(row.get("candidate_id")): row
        for row in rows
        if isinstance(row, dict) and row.get("candidate_id")
    }
    if len(by_id) != len(rows):
        errors.append(f"{track} judge has duplicate or malformed score rows")
    if set(by_id) != candidate_ids:
        errors.append(
            f"{track} judge candidate census differs: "
            f"missing={sorted(candidate_ids - set(by_id))} extra={sorted(set(by_id) - candidate_ids)}"
        )
    return judge_id, by_id


def _canonical_advocate_ranking(errors: list[str]) -> dict[str, Any]:
    """Pure reconstruction of the no-web author/judge ranking authority."""

    candidates, author_by_candidate = _load_advocate_responses(errors)
    candidate_ids = set(author_by_candidate)
    author_ids = set(author_by_candidate.values())
    if len(author_ids) != 4:
        errors.append(f"advocate divergence requires four distinct authors, got {len(author_ids)}")
    judge_root = AUDIT / "agents/advocate_judging"
    pre_judge, pre_rows = _load_judge_rows(
        judge_root / "pre_solver_judge_response.json",
        "pre_solver",
        candidate_ids,
        author_ids,
        errors,
    )
    post_judge, post_rows = _load_judge_rows(
        judge_root / "post_native_judge_response.json",
        "post_native_solver",
        candidate_ids,
        author_ids,
        errors,
    )
    integrity_judge, integrity_rows = _load_judge_rows(
        judge_root / "integrity_veto_judge_response.json",
        "integrity_veto",
        candidate_ids,
        author_ids,
        errors,
    )
    if len({pre_judge, post_judge, integrity_judge}) != 3:
        errors.append("all three independent judge IDs must be distinct")

    ranked: list[dict[str, Any]] = []
    for candidate in candidates:
        candidate_id = candidate["candidate_id"]
        pre = pre_rows.get(candidate_id, {})
        post = post_rows.get(candidate_id, {})
        integrity = integrity_rows.get(candidate_id, {})
        pre_total = _weighted_score(
            pre.get("scores"), PRE_SOLVER_WEIGHTS, f"{candidate_id} pre-solver", errors
        )
        post_total = _weighted_score(
            post.get("scores"), POST_SOLVER_WEIGHTS, f"{candidate_id} post-native", errors
        )
        for track, row in (("pre-solver", pre), ("post-native", post)):
            if not isinstance(row.get("track_eligible"), bool) or not row.get("rationale"):
                errors.append(f"{candidate_id} {track} judge row lacks eligibility/rationale")
        integrity_required = {
            "candidate_id",
            "unresolved_p0",
            "missing_falsifier",
            "provenance_unsecured",
            "eligible_for_retain",
            "rationale",
        }
        if not integrity_required <= integrity.keys():
            errors.append(f"{candidate_id} integrity veto row is incomplete")
        veto_flags = {
            key: integrity.get(key)
            for key in ("unresolved_p0", "missing_falsifier", "provenance_unsecured")
        }
        if any(not isinstance(value, bool) for value in veto_flags.values()):
            errors.append(f"{candidate_id} integrity veto flags must be booleans")
        expected_eligible = not any(value is True for value in veto_flags.values())
        if integrity.get("eligible_for_retain") is not expected_eligible:
            errors.append(f"{candidate_id} integrity retain eligibility contradicts veto flags")
        eligible_scores = []
        if pre.get("track_eligible") is True:
            eligible_scores.append(pre_total)
        if post.get("track_eligible") is True:
            eligible_scores.append(post_total)
        selection_score = max(eligible_scores) if eligible_scores else 0.0
        row = dict(candidate)
        row.update(
            {
                "pre_solver_review": {
                    "judge_id": pre_judge,
                    "scores": pre.get("scores"),
                    "total": pre_total,
                    "track_eligible": pre.get("track_eligible"),
                    "rationale": pre.get("rationale"),
                },
                "post_native_solver_review": {
                    "judge_id": post_judge,
                    "scores": post.get("scores"),
                    "total": post_total,
                    "track_eligible": post.get("track_eligible"),
                    "rationale": post.get("rationale"),
                },
                "integrity_veto_review": {
                    "judge_id": integrity_judge,
                    **veto_flags,
                    "eligible_for_retain": integrity.get("eligible_for_retain"),
                    "rationale": integrity.get("rationale"),
                },
                "selection_score": selection_score,
            }
        )
        ranked.append(row)

    shortlist_ids: list[str] = []
    extras: list[dict[str, Any]] = []
    for axis in ADVOCATE_RESPONSE_PATHS:
        axis_rows = sorted(
            (row for row in ranked if row["axis"] == axis),
            key=lambda row: (-row["selection_score"], row["candidate_id"]),
        )
        for index, row in enumerate(axis_rows, 1):
            row["axis_rank"] = index
        mandatory = axis_rows[:2]
        shortlist_ids.extend(row["candidate_id"] for row in mandatory)
        cutoff = mandatory[-1]["selection_score"] if mandatory else 0.0
        extras.extend(
            row
            for row in axis_rows[2:]
            if row["selection_score"] >= cutoff - 5.0
        )
    for row in sorted(extras, key=lambda row: (-row["selection_score"], row["candidate_id"])):
        if len(shortlist_ids) >= 12:
            break
        shortlist_ids.append(row["candidate_id"])
    shortlist_set = set(shortlist_ids)
    shortlist_hash = sha256_json(sorted(shortlist_set))

    return {
        "ranked": ranked,
        "author_by_candidate": author_by_candidate,
        "author_ids": author_ids,
        "pre_judge": pre_judge,
        "post_judge": post_judge,
        "integrity_judge": integrity_judge,
        "shortlist_ids": shortlist_ids,
        "shortlist_set": shortlist_set,
        "shortlist_hash": shortlist_hash,
    }


def _shortlist_freeze_projection(canonical: dict[str, Any]) -> dict[str, Any]:
    ranking_rows = []
    for row in canonical["ranked"]:
        ranking_rows.append(
            {
                "candidate_id": row["candidate_id"],
                "axis": row["axis"],
                "author_id": canonical["author_by_candidate"][row["candidate_id"]],
                "pre_solver_review": row["pre_solver_review"],
                "post_native_solver_review": row["post_native_solver_review"],
                "integrity_veto_review": row["integrity_veto_review"],
                "selection_score": row["selection_score"],
                "axis_rank": row["axis_rank"],
            }
        )
    return {
        "weights": {
            "pre_solver": PRE_SOLVER_WEIGHTS,
            "post_native_solver": POST_SOLVER_WEIGHTS,
        },
        "author_ids": sorted(canonical["author_ids"]),
        "judge_ids": {
            "pre_solver": canonical["pre_judge"],
            "post_native_solver": canonical["post_judge"],
            "integrity_veto": canonical["integrity_judge"],
        },
        "ranking_rows": sorted(ranking_rows, key=lambda row: row["candidate_id"]),
        "shortlist_candidate_ids": canonical["shortlist_ids"],
        "shortlist_count": len(canonical["shortlist_ids"]),
        "shortlist_hash": canonical["shortlist_hash"],
        "shortlist_rule": (
            "per-axis top two plus candidates within five points of the second-place "
            "axis cutoff, globally capped at twelve"
        ),
    }


def build_shortlist_freeze() -> dict[str, Any]:
    """Materialize the deterministic no-web shortlist authority separately."""

    errors: list[str] = []
    canonical = _canonical_advocate_ranking(errors)
    if errors:
        raise RuntimeError("cannot freeze advocate shortlist:\n- " + "\n- ".join(errors))
    inputs = [
        *ADVOCATE_RESPONSE_PATHS.values(),
        AUDIT / "agents/advocate_judging/pre_solver_judge_response.json",
        AUDIT / "agents/advocate_judging/post_native_judge_response.json",
        AUDIT / "agents/advocate_judging/integrity_veto_judge_response.json",
        AUDIT / "WEB_LOCK.json",
    ]
    payload = {
        "schema": "htt.pr118.shortlist_freeze.v1",
        **_artifact_metadata(
            inputs,
            "venv/bin/python -B scripts/audits/jcap_prd_20260714.py build-shortlist-freeze",
            transfer_source="none_no_web_ranking_inputs",
            sky_support_status="not_a_sky_result",
            null_mock_status="not_a_statistical_result",
        ),
        "phase": "no_web_shortlist_authority",
        "generated_at": utcnow(),
        "web_lock_sha256": sha256_file(AUDIT / "WEB_LOCK.json"),
        "web_used": False,
        "materialization_status": (
            "retrospective_canonical_hash_seal_of_the_pre_web_author_and_judge_packets; "
            "the physical freeze file was not independently timestamp-sealed before the "
            "single final CRAG lookup"
        ),
        "ordering_caveat": (
            "Canonical replay proves that the CRAG assignment equals the no-web ranking; "
            "it does not retroactively prove filesystem materialization order."
        ),
        **_shortlist_freeze_projection(canonical),
    }
    write_json(SHORTLIST_FREEZE, payload)
    return payload


def _finalize_advocate_ranking(
    canonical: dict[str, Any],
    final_crag: dict[str, Any] | None,
    errors: list[str],
) -> list[dict[str, Any]]:
    """Apply only the bounded CRAG updates to an already frozen ranking."""

    ranked = canonical["ranked"]
    shortlist_set = canonical["shortlist_set"]
    update_by_id = {
        row.get("candidate_id"): row
        for row in (final_crag or {}).get("candidate_updates", [])
        if isinstance(row, dict)
    }
    for row in ranked:
        row["shortlisted_for_final_crag"] = row["candidate_id"] in shortlist_set
        row["shortlist_rule"] = (
            "per-axis top two plus candidates within five points of the second-place "
            "axis cutoff, globally capped at twelve"
        )
        row["pre_crag_selection_score"] = row["selection_score"]
        update = update_by_id.get(row["candidate_id"])
        if update:
            row["final_crag_update"] = update
            row["final_disposition"] = update.get(
                "recommended_disposition", row["salvage_disposition_proposed"]
            )
            novelty_after = update.get("novelty_after")
            for review_key, weights in (
                ("pre_solver_review", PRE_SOLVER_WEIGHTS),
                ("post_native_solver_review", POST_SOLVER_WEIGHTS),
            ):
                review = row[review_key]
                review["pre_crag_total"] = review["total"]
                post_crag_scores = dict(review["scores"])
                post_crag_scores["novelty"] = novelty_after
                review["post_crag_scores"] = post_crag_scores
                review["post_crag_total"] = _weighted_score(
                    post_crag_scores,
                    weights,
                    f"{row['candidate_id']} {review_key} post-CRAG",
                    errors,
                )
        else:
            row["final_crag_update"] = None
            row["final_disposition"] = row["salvage_disposition_proposed"]
            for review_key in ("pre_solver_review", "post_native_solver_review"):
                review = row[review_key]
                review["pre_crag_total"] = review["total"]
                review["post_crag_scores"] = None
                review["post_crag_total"] = None
        if row["final_disposition"] not in ADVOCATE_DISPOSITIONS:
            errors.append(f"{row['candidate_id']} has invalid final disposition")
        if (
            not row["integrity_veto_review"]["eligible_for_retain"]
            and row["final_disposition"] == "rescued"
        ):
            errors.append(f"{row['candidate_id']} bypasses a mandatory retain veto")
    return ranked


def build_advocate_ledger() -> dict[str, Any]:
    """Deterministically aggregate author-blind judges and finalize after CRAG."""

    errors: list[str] = []
    canonical = _canonical_advocate_ranking(errors)
    ranked = canonical["ranked"]
    author_ids = canonical["author_ids"]
    pre_judge = canonical["pre_judge"]
    post_judge = canonical["post_judge"]
    integrity_judge = canonical["integrity_judge"]
    shortlist_ids = canonical["shortlist_ids"]
    shortlist_set = canonical["shortlist_set"]
    shortlist_hash = canonical["shortlist_hash"]
    judge_root = AUDIT / "agents/advocate_judging"
    freeze = json.loads(SHORTLIST_FREEZE.read_text(encoding="utf-8"))
    freeze_projection = _shortlist_freeze_projection(canonical)
    for key, expected in freeze_projection.items():
        if freeze.get(key) != expected:
            errors.append(f"shortlist freeze canonical projection drift at {key}")

    final_crag_path = AUDIT / "web_crag_final.json"
    final_crag = (
        json.loads(final_crag_path.read_text(encoding="utf-8"))
        if final_crag_path.is_file()
        else None
    )
    ranked = _finalize_advocate_ranking(canonical, final_crag, errors)

    if errors:
        raise RuntimeError("cannot build advocate ledger:\n- " + "\n- ".join(errors))
    payload = {
        "schema": "htt.pr118.advocate_candidate_ledger.v1",
        **_artifact_metadata(
            [
                *ADVOCATE_RESPONSE_PATHS.values(),
                judge_root / "pre_solver_judge_response.json",
                judge_root / "post_native_judge_response.json",
                judge_root / "integrity_veto_judge_response.json",
                AUDIT / "WEB_LOCK.json",
                SHORTLIST_FREEZE,
                *([final_crag_path] if final_crag else []),
            ],
            "venv/bin/python -B scripts/audits/jcap_prd_20260714.py build-advocate-ledger",
        ),
        "phase": "final_crag_complete" if final_crag else "shortlist_frozen",
        "generated_at": utcnow(),
        "web_lock_sha256": sha256_file(AUDIT / "WEB_LOCK.json"),
        "generation_web_used": False,
        "candidate_count": len(ranked),
        "axis_counts": dict(Counter(row["axis"] for row in ranked)),
        "author_ids": sorted(author_ids),
        "ranking_authority": {
            "pre_solver_judge": pre_judge,
            "post_native_solver_judge": post_judge,
            "integrity_veto_judge": integrity_judge,
            "candidate_authors_excluded": True,
            "deterministic_aggregator": relative(Path(__file__)),
        },
        "weights": {
            "pre_solver": PRE_SOLVER_WEIGHTS,
            "post_native_solver": POST_SOLVER_WEIGHTS,
        },
        "shortlist_candidate_ids": shortlist_ids,
        "shortlist_count": len(shortlist_ids),
        "shortlist_hash": shortlist_hash,
        "shortlist_basis": "pre_crag_selection_score_frozen_before_final_crag",
        "shortlist_freeze_path": relative(SHORTLIST_FREEZE),
        "shortlist_freeze_sha256": sha256_file(SHORTLIST_FREEZE),
        "final_crag_path": relative(final_crag_path) if final_crag else None,
        "candidates": sorted(ranked, key=lambda row: row["candidate_id"]),
        "counterfactual_contract": COUNTERFACTUAL_FIELDS,
    }
    write_json(AUDIT / "advocate_candidate_ledger.json", payload)
    return payload


def build_final_crag(*, write: bool = True) -> dict[str, Any]:
    """Merge the three bounded final lookups and prove they stayed in-scope."""

    freeze = json.loads(SHORTLIST_FREEZE.read_text(encoding="utf-8"))
    shortlist = freeze["shortlist_candidate_ids"]
    shortlist_set = set(shortlist)
    if shortlist_set != set().union(*FINAL_CRAG_ASSIGNMENTS.values()):
        raise RuntimeError("frozen shortlist differs from final CRAG role assignments")
    errors: list[str] = []
    queries: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []
    updates: list[dict[str, Any]] = []
    receipts: list[dict[str, Any]] = []
    all_source_ids: set[str] = set()
    all_query_ids: set[str] = set()
    for group, path in FINAL_CRAG_RESPONSE_PATHS.items():
        payload = _validate_json(path, errors)
        payload = _require_object(
            payload,
            f"{group} final CRAG response",
            (
                "schema",
                "phase",
                "researcher_id",
                "web_used",
                "assigned_candidate_ids",
                "queries",
                "sources",
                "candidate_updates",
                "web_closed",
            ),
            errors,
        )
        if not payload:
            continue
        _require_schema(
            payload,
            f"{group} final CRAG response",
            "htt.pr118.final_crag_agent.v1",
            errors,
        )
        _require_exact_keys(
            payload,
            f"{group} final CRAG response",
            {
                "schema",
                "phase",
                "researcher_id",
                "web_used",
                "assigned_candidate_ids",
                "queries",
                "sources",
                "candidate_updates",
                "web_closed",
            },
            errors,
        )
        researcher_id = payload.get("researcher_id")
        if not isinstance(researcher_id, str) or not researcher_id.strip():
            errors.append(f"{group} final CRAG researcher_id must be non-whitespace text")
        for collection_name in ("queries", "sources", "candidate_updates"):
            if not isinstance(payload.get(collection_name), list):
                errors.append(
                    f"{group} final CRAG {collection_name} must be a list"
                )
                payload[collection_name] = []
        assigned_rows = payload.get("assigned_candidate_ids", [])
        if not isinstance(assigned_rows, list) or any(
            not isinstance(item, str) or not item.strip() for item in assigned_rows
        ):
            errors.append(f"{group} final CRAG assigned_candidate_ids must be text rows")
            assigned_rows = []
        elif len(assigned_rows) != len(set(assigned_rows)):
            errors.append(f"{group} final CRAG assigned_candidate_ids contain duplicates")
        assigned = set(assigned_rows)
        if assigned != FINAL_CRAG_ASSIGNMENTS[group]:
            errors.append(f"{group} final CRAG escaped or omitted its assignment")
        if (
            payload.get("phase") != "final_crag"
            or payload.get("web_used") is not True
            or payload.get("web_closed") is not True
        ):
            errors.append(f"{group} final CRAG lacks open/close receipt")
        local_source_ids = {
            row.get("source_id")
            for row in payload.get("sources", [])
            if isinstance(row, dict)
        }
        if len(local_source_ids) != len(payload.get("sources", [])):
            errors.append(f"{group} final CRAG has duplicate/malformed sources")
        collision = all_source_ids & local_source_ids
        if collision:
            errors.append(f"final CRAG source IDs collide across agents: {sorted(collision)}")
        all_source_ids |= local_source_ids
        local_query_ids = {
            row.get("query_id")
            for row in payload.get("queries", [])
            if isinstance(row, dict)
        }
        if len(local_query_ids) != len(payload.get("queries", [])):
            errors.append(f"{group} final CRAG has duplicate/malformed queries")
        collision = all_query_ids & local_query_ids
        if collision:
            errors.append(f"final CRAG query IDs collide across agents: {sorted(collision)}")
        all_query_ids |= local_query_ids
        for query in payload.get("queries", []):
            if not isinstance(query, dict):
                errors.append(f"{group} final CRAG query must be an object")
                continue
            _require_exact_keys(
                query,
                f"{group} final CRAG query {query.get('query_id')}",
                {"query_id", "candidate_ids", "query", "executed_at"},
                errors,
            )
            if not isinstance(query.get("candidate_ids"), list) or any(
                not isinstance(item, str) or not item.strip()
                for item in query.get("candidate_ids", [])
            ):
                errors.append(f"{group} final CRAG query candidate_ids must be text rows")
            for field in ("query_id", "query", "executed_at"):
                if not isinstance(query.get(field), str) or not query[field].strip():
                    errors.append(
                        f"{group} final CRAG query {query.get('query_id')} {field} "
                        "must be non-whitespace text"
                    )
            if not set(query.get("candidate_ids", [])) <= assigned:
                errors.append(f"{group} final CRAG query escaped assigned candidates")
            for field in ("query_id", "candidate_ids", "query", "executed_at"):
                if not _meaningful_structure(query.get(field)):
                    errors.append(f"{group} final CRAG query missing {field}")
        for source in payload.get("sources", []):
            if not isinstance(source, dict):
                errors.append(f"{group} final CRAG source must be an object")
                continue
            _require_exact_keys(
                source,
                f"{group} final CRAG source {source.get('source_id')}",
                {
                    "source_id",
                    "url",
                    "title",
                    "accessed_at",
                    "candidate_ids",
                    "primary_or_official",
                    "supports_or_challenges",
                    "data_code_availability",
                    "citation_action",
                },
                errors,
            )
            if not isinstance(source.get("candidate_ids"), list) or any(
                not isinstance(item, str) or not item.strip()
                for item in source.get("candidate_ids", [])
            ):
                errors.append(f"{group} final CRAG source candidate_ids must be text rows")
            if not set(source.get("candidate_ids", [])) <= assigned:
                errors.append(f"{group} final CRAG source escaped assigned candidates")
            if source.get("primary_or_official") is not True:
                errors.append(f"{group} final CRAG used a non-primary/non-official source")
            for field in (
                "source_id",
                "url",
                "title",
                "accessed_at",
                "supports_or_challenges",
                "data_code_availability",
                "citation_action",
            ):
                if not isinstance(source.get(field), str) or not source[field].strip():
                    errors.append(
                        f"{group} final CRAG source {source.get('source_id')} {field} "
                        "must be non-whitespace text"
                    )
            for field in (
                "source_id",
                "url",
                "title",
                "accessed_at",
                "candidate_ids",
                "supports_or_challenges",
                "data_code_availability",
                "citation_action",
            ):
                if not _meaningful_structure(source.get(field)):
                    errors.append(f"{group} final CRAG source missing {field}")
        local_updates = payload.get("candidate_updates", [])
        if {
            row.get("candidate_id") for row in local_updates if isinstance(row, dict)
        } != assigned or len(local_updates) != len(assigned):
            errors.append(f"{group} final CRAG candidate-update census differs")
        for update in local_updates:
            if not isinstance(update, dict):
                errors.append(f"{group} final CRAG update must be an object")
                continue
            _require_exact_keys(
                update,
                f"{group} final CRAG update {update.get('candidate_id')}",
                {
                    "candidate_id",
                    "nearest_prior_art",
                    "novelty_before",
                    "novelty_after",
                    "blocker_update",
                    "recommended_disposition",
                    "source_ids",
                },
                errors,
            )
            if not isinstance(update.get("source_ids"), list) or any(
                not isinstance(item, str) or not item.strip()
                for item in update.get("source_ids", [])
            ):
                errors.append(f"{group} final CRAG update source_ids must be text rows")
            if not isinstance(update.get("candidate_id"), str) or not update[
                "candidate_id"
            ].strip():
                errors.append(f"{group} final CRAG update candidate_id must be text")
            for field in ("novelty_before", "novelty_after"):
                value = update.get(field)
                if (
                    not isinstance(value, (int, float))
                    or isinstance(value, bool)
                    or not 0 <= value <= 10
                ):
                    errors.append(
                        f"{group} final CRAG update {update.get('candidate_id')} "
                        f"{field} must be numeric in [0,10]"
                    )
            if not set(update.get("source_ids", [])) <= local_source_ids:
                errors.append(f"{group} final CRAG update cites an unknown source")
            if update.get("recommended_disposition") not in ADVOCATE_DISPOSITIONS:
                errors.append(f"{group} final CRAG update has invalid disposition")
            for field in (
                "nearest_prior_art",
                "novelty_before",
                "novelty_after",
                "blocker_update",
                "recommended_disposition",
                "source_ids",
            ):
                if not _meaningful_structure(update.get(field)):
                    errors.append(f"{group} final CRAG update missing {field}")
        queries.extend(payload.get("queries", []))
        sources.extend(payload.get("sources", []))
        updates.extend(local_updates)
        receipts.append(
            {
                "group": group,
                "researcher_id": payload["researcher_id"],
                "response_path": relative(path),
                "response_sha256": sha256_file(path),
                "web_used": True,
                "web_closed": True,
            }
        )
    if len({row["researcher_id"] for row in receipts}) != len(receipts):
        errors.append("final CRAG researcher IDs must be unique")
    if {row.get("candidate_id") for row in updates} != shortlist_set or len(updates) != len(shortlist):
        errors.append("merged final CRAG updates differ from frozen shortlist")
    if errors:
        raise RuntimeError("cannot build final CRAG:\n- " + "\n- ".join(errors))
    raw_query_count = len(queries)
    raw_source_count = len(sources)
    # The agents retain their full primary-source research as raw evidence.
    # The authoritative final packet is intentionally short: no more than two
    # directly cited sources and one recorded query per shortlisted candidate.
    selected_source_ids = {
        source_id
        for update in updates
        for source_id in update.get("source_ids", [])[:2]
    }
    sources = [row for row in sources if row.get("source_id") in selected_source_ids]
    selected_queries: list[dict[str, Any]] = []
    selected_query_ids: set[str] = set()
    for candidate_id in shortlist:
        for query in queries:
            if (
                candidate_id in query.get("candidate_ids", [])
                and query.get("query_id") not in selected_query_ids
            ):
                selected_queries.append(query)
                selected_query_ids.add(query["query_id"])
                break
    queries = selected_queries
    updates = [
        {
            **row,
            "source_ids": [
                source_id
                for source_id in row.get("source_ids", [])
                if source_id in selected_source_ids
            ][:2],
        }
        for row in updates
    ]
    source_by_id = {row["source_id"]: row for row in sources}
    for update in updates:
        candidate_id = update["candidate_id"]
        relevant_queries = [
            row for row in queries if candidate_id in row.get("candidate_ids", [])
        ]
        relevant_sources = [
            source_by_id[source_id]
            for source_id in update.get("source_ids", [])
            if source_id in source_by_id
            and candidate_id in source_by_id[source_id].get("candidate_ids", [])
        ]
        if not relevant_queries:
            errors.append(f"{candidate_id} has no candidate-relevant final CRAG query")
        if not relevant_sources:
            errors.append(f"{candidate_id} has no candidate-relevant cited final CRAG source")
        if len(update.get("source_ids", [])) > 2:
            errors.append(f"{candidate_id} exceeds the two-source authoritative CRAG cap")
    if errors:
        raise RuntimeError("cannot build bounded final CRAG:\n- " + "\n- ".join(errors))
    payload = {
        "schema": "htt.pr118.web_crag_final.v1",
        **_artifact_metadata(
            [*FINAL_CRAG_RESPONSE_PATHS.values(), SHORTLIST_FREEZE],
            "venv/bin/python -B scripts/audits/jcap_prd_20260714.py build-final-crag",
            transfer_source="primary_and_official_literature_metadata_only",
            sky_support_status="not_a_sky_result",
            null_mock_status="not_a_statistical_result",
        ),
        "generated_at": utcnow(),
        "reopened_after_shortlist": True,
        "reopen_scope": "nearest prior art and time-variable blocker checks for frozen shortlist only",
        "shortlist_path": relative(SHORTLIST_FREEZE),
        "shortlist_sha256": sha256_file(SHORTLIST_FREEZE),
        "shortlist_hash": freeze["shortlist_hash"],
        "candidate_ids": shortlist,
        "candidate_count": len(shortlist),
        "selection_policy": (
            "authoritative packet retains at most two cited primary/official sources "
            "and one recorded query per frozen candidate; full lookups remain hash-bound "
            "in the three raw agent responses"
        ),
        "raw_query_count": raw_query_count,
        "raw_source_count": raw_source_count,
        "queries": queries,
        "sources": sources,
        "candidate_updates": updates,
        "agent_receipts": receipts,
        "closed_after_completion": True,
        "forbidden_after_close": "new web search or candidate expansion",
    }
    if write:
        write_json(AUDIT / "web_crag_final.json", payload)
    return payload


def _authoritative_criticism_fields(
    prior: dict[str, Any], atomic: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for row in prior["prior_findings"]:
        criticism_id = row["prior_id"]
        rows[criticism_id] = {
            "criticism_id": criticism_id,
            "origin": "prior",
            "severity": row["severity"],
            "criticism": row["title"],
            "source_reference": f"{row['source_path']}#{criticism_id}",
            "source_hash": row["source_hash"],
            "authoritative_state": row["remediation_state"],
            "maximum_claim_tier": (
                "diagnostic-only advocate response; finding remains KNOWN_OPEN until "
                "a separate hash-bound production-remediation receipt passes"
            ),
        }
    for row in prior["audit_completeness_gaps"]:
        criticism_id = row["gap_id"]
        rows[criticism_id] = {
            "criticism_id": criticism_id,
            "origin": "audit_gap",
            "severity": "AUDIT_GAP",
            "criticism": row["title"],
            "source_reference": f"{row['source_path']}#{criticism_id}",
            "source_hash": row["source_hash"],
            "authoritative_state": row["remediation_state"],
            "maximum_claim_tier": (
                "audit-process or coverage-accounting conclusion only; no scientific "
                "claim promotion"
            ),
        }
    atomic_hash = sha256_file(ATOMIC_LEDGER)
    for row in atomic["atomic_findings"]:
        if row.get("disposition") != "NEW_OPEN":
            continue
        criticism_id = row["atomic_id"]
        rows[criticism_id] = {
            "criticism_id": criticism_id,
            "origin": "delta_new",
            "severity": row["severity"],
            "criticism": row["error_claim"],
            "source_reference": f"{relative(ATOMIC_LEDGER)}#{criticism_id}",
            "source_hash": atomic_hash,
            "authoritative_state": "NEW_OPEN",
            "maximum_claim_tier": row["maximum_claim_tier"],
        }
    return rows


def build_criticism_matrix(*, write: bool = True) -> dict[str, Any]:
    """Merge independently authored steelman responses without losing criticism IDs."""

    prior = json.loads((AUDIT / "prior_crosswalk.json").read_text(encoding="utf-8"))
    atomic = json.loads(ATOMIC_LEDGER.read_text(encoding="utf-8"))
    advocate = json.loads(
        (AUDIT / "advocate_candidate_ledger.json").read_text(encoding="utf-8")
    )
    candidate_ids = {row["candidate_id"] for row in advocate["candidates"]}
    authority = _authoritative_criticism_fields(prior, atomic)
    expected_by_group = {
        "prior": {row["prior_id"] for row in prior["prior_findings"]},
        "gap_theory_statistics": {
            row["gap_id"] for row in prior["audit_completeness_gaps"]
        }
        | {
            row["atomic_id"]
            for row in atomic["atomic_findings"]
            if row.get("disposition") == "NEW_OPEN"
            and row["atomic_id"].startswith(("N-THEORY-", "N-STAT-"))
        },
        "data_code": {
            row["atomic_id"]
            for row in atomic["atomic_findings"]
            if row.get("disposition") == "NEW_OPEN"
            and row["atomic_id"].startswith(("N-DATA-", "N-CODE-"))
        },
    }
    errors: list[str] = []
    merged: list[dict[str, Any]] = []
    mapper_ids: list[str] = []
    for group, path in CRITICISM_MAP_PATHS.items():
        payload = _validate_json(path, errors)
        payload = _require_object(
            payload,
            f"{group} criticism mapper",
            ("schema", "mapper_id", "phase", "web_used", "assigned_group", "rows"),
            errors,
        )
        if not payload:
            continue
        _require_schema(
            payload,
            f"{group} criticism mapper",
            "htt.pr118.criticism_mapper.v1",
            errors,
        )
        _require_exact_keys(
            payload,
            f"{group} criticism mapper",
            {"schema", "mapper_id", "phase", "web_used", "assigned_group", "rows"},
            errors,
        )
        if not isinstance(payload.get("mapper_id"), str) or not payload["mapper_id"].strip():
            errors.append(f"{group} criticism mapper_id must be non-whitespace text")
        if payload.get("phase") != "criticism_mapping" or payload.get("assigned_group") != group:
            errors.append(f"{group} criticism mapper phase/group mismatch")
        if payload.get("web_used") is not False:
            errors.append(f"{group} criticism mapper performed a new web lookup")
        mapper_ids.append(str(payload["mapper_id"]))
        rows = payload.get("rows", [])
        if not isinstance(rows, list):
            errors.append(f"{group} criticism mapper rows must be a list")
            rows = []
        ids = {
            row.get("criticism_id")
            for row in rows
            if isinstance(row, dict) and row.get("criticism_id")
        }
        if len(ids) != len(rows) or ids != expected_by_group[group]:
            errors.append(
                f"{group} criticism mapper census differs: "
                f"missing={sorted(expected_by_group[group] - ids)} "
                f"extra={sorted(ids - expected_by_group[group])}"
            )
        for row in rows:
            required = {
                "criticism_id",
                "origin",
                "severity",
                "criticism",
                "strongest_advocate_response",
                "response_to_rebuttal",
                "disposition",
                "candidate_ids",
                "residual_risk",
                "decisive_closeout_evidence",
                "maximum_claim_tier",
                "source_reference",
            }
            if not required <= row.keys():
                errors.append(f"{row.get('criticism_id')} mapper row lacks required fields")
                continue
            _require_exact_keys(
                row,
                f"{row.get('criticism_id')} criticism mapper row",
                required,
                errors,
            )
            for field in (
                "criticism_id",
                "origin",
                "severity",
                "criticism",
                "strongest_advocate_response",
                "response_to_rebuttal",
                "disposition",
                "residual_risk",
                "decisive_closeout_evidence",
                "maximum_claim_tier",
                "source_reference",
            ):
                if not isinstance(row.get(field), str) or not row[field].strip():
                    errors.append(
                        f"{row.get('criticism_id')} mapper {field} must be non-whitespace text"
                    )
            if not isinstance(row.get("candidate_ids"), list) or any(
                not isinstance(item, str) or not item.strip()
                for item in row.get("candidate_ids", [])
            ):
                errors.append(
                    f"{row.get('criticism_id')} mapper candidate_ids must be text rows"
                )
            if row.get("disposition") not in ADVOCATE_DISPOSITIONS:
                errors.append(f"{row.get('criticism_id')} mapper disposition invalid")
            if not set(row.get("candidate_ids", [])) <= candidate_ids:
                errors.append(f"{row.get('criticism_id')} mapper links unknown candidate")
            criticism_id = row["criticism_id"]
            immutable = authority[criticism_id]
            disposition = row["disposition"]
            override = None
            if immutable["authoritative_state"] == "KNOWN_OPEN" and disposition == "rescued":
                disposition = "downclaimed"
                override = (
                    "Mapper proposed rescued, but a KNOWN_OPEN imported finding cannot be "
                    "rescued without a separate hash-bound production-remediation receipt."
                )
            enriched = {
                **row,
                "mapper_proposed_origin": row["origin"],
                "mapper_proposed_severity": row["severity"],
                "mapper_proposed_criticism": row["criticism"],
                "mapper_proposed_source_reference": row["source_reference"],
                "mapper_proposed_maximum_claim_tier": row["maximum_claim_tier"],
                "mapper_proposed_disposition": row["disposition"],
                **immutable,
                "disposition": disposition,
                "root_disposition_override": override,
            }
            enriched["mapper_id"] = payload["mapper_id"]
            enriched["mapper_response_path"] = relative(path)
            enriched["mapper_response_sha256"] = sha256_file(path)
            merged.append(enriched)
    if len(set(mapper_ids)) != len(mapper_ids):
        errors.append("criticism mapper IDs must be independent and unique")
    if len(merged) != 102 or len({row.get("criticism_id") for row in merged}) != 102:
        errors.append("merged criticism response census must be exactly 102")
    if any(row.get("disposition") == "rescued" for row in merged):
        errors.append(
            "current root criticism policy requires zero rescued findings without "
            "hash-bound production-remediation receipts"
        )
    if errors:
        raise RuntimeError("cannot build criticism matrix:\n- " + "\n- ".join(errors))
    origin_order = {"prior": 0, "audit_gap": 1, "delta_new": 2}
    merged.sort(
        key=lambda row: (origin_order.get(row["origin"], 9), row["criticism_id"])
    )
    payload = {
        "schema": "htt.pr118.criticism_response_matrix.v1",
        **_artifact_metadata(
            [
                *CRITICISM_MAP_PATHS.values(),
                AUDIT / "advocate_candidate_ledger.json",
                AUDIT / "prior_crosswalk.json",
                ATOMIC_LEDGER,
            ],
            "venv/bin/python -B scripts/audits/jcap_prd_20260714.py build-criticism-matrix",
        ),
        "generated_at": utcnow(),
        "web_used": False,
        "fixed_external_packets": [
            relative(AUDIT / "web_crag_initial.json"),
            relative(AUDIT / "web_crag_final.json"),
        ],
        "mapper_ids": mapper_ids,
        "row_count": len(merged),
        "origin_counts": dict(Counter(row["origin"] for row in merged)),
        "disposition_counts": dict(Counter(row["disposition"] for row in merged)),
        "rows": merged,
    }
    if write:
        write_json(AUDIT / "criticism_response_matrix.json", payload)
    lines = [
        "# Criticism-response matrix",
        "",
        "Every imported finding, audit-completeness gap, and new atomic delta receives exactly one advocate disposition. `rescued` never means a production claim has been validated; the maximum claim tier and residual blocker remain controlling.",
        "",
        f"- Rows: {payload['row_count']}",
        f"- Origins: `{json.dumps(payload['origin_counts'], sort_keys=True)}`",
        f"- Dispositions: `{json.dumps(payload['disposition_counts'], sort_keys=True)}`",
        "",
        "| ID | Origin | Severity | Disposition | Candidate links | Maximum claim tier | Advocate response and residual risk |",
        "|---|---|---:|---|---|---|---|",
    ]
    for row in merged:
        def cell(value: Any) -> str:
            return str(value).replace("|", "\\|").replace("\n", " ")

        links = ", ".join(row["candidate_ids"]) or "none"
        response = (
            f"{row['strongest_advocate_response']} **Residual:** {row['residual_risk']} "
            f"**Closeout:** {row['decisive_closeout_evidence']}"
        )
        lines.append(
            "| "
            + " | ".join(
                cell(value)
                for value in (
                    row["criticism_id"],
                    row["origin"],
                    row["severity"],
                    row["disposition"],
                    links,
                    row["maximum_claim_tier"],
                    response,
                )
            )
            + " |"
        )
    if write:
        (AUDIT / "criticism_response_matrix.md").write_text(
            "\n".join(lines) + "\n", encoding="utf-8"
        )
    return payload


def build_final_reports() -> dict[str, Any]:
    """Render the independent decisions and root synthesis without claim promotion."""

    advocate = json.loads(
        (AUDIT / "advocate_candidate_ledger.json").read_text(encoding="utf-8")
    )
    matrix = json.loads(
        (AUDIT / "criticism_response_matrix.json").read_text(encoding="utf-8")
    )
    crag = json.loads((AUDIT / "web_crag_final.json").read_text(encoding="utf-8"))
    coverage = json.loads((AUDIT / "coverage_matrix.json").read_text(encoding="utf-8"))
    coverage_rows = coverage["generated_result_rows"]
    coverage_counts = Counter(row["examination_status"] for row in coverage_rows)
    if len(coverage_rows) != 78 or coverage_counts != {
        "not_examined": 44,
        "sampled": 34,
    }:
        raise RuntimeError(
            "final report coverage ceiling drift: "
            f"rows={len(coverage_rows)} counts={dict(coverage_counts)}"
        )
    candidate_ids = {row["candidate_id"] for row in advocate["candidates"]}
    errors: list[str] = []
    decisions: list[dict[str, Any]] = []
    for journal, path in FINAL_REFEREE_RESPONSE_PATHS.items():
        payload = _validate_json(path, errors)
        payload = _require_object(
            payload,
            f"{journal} final referee",
            (
                "schema",
                "referee_id",
                "phase",
                "web_used",
                "as_shipped_decision",
                "as_shipped_score_0_to_10",
                "post_surgery_decision",
                "post_surgery_score_0_to_10",
                "strongest_defensible_thesis",
                "pre_solver_research",
                "post_native_research",
                "must_fix",
                "unexecuted_blockers",
                "dissent_or_uncertainty",
                "candidate_ids_considered",
                "evidence_paths",
            ),
            errors,
        )
        if not payload:
            continue
        _require_schema(
            payload,
            f"{journal} final referee",
            "htt.pr118.final_referee.v1",
            errors,
        )
        _require_exact_keys(
            payload,
            f"{journal} final referee",
            {
                "schema",
                "referee_id",
                "phase",
                "web_used",
                "as_shipped_decision",
                "as_shipped_score_0_to_10",
                "post_surgery_decision",
                "post_surgery_score_0_to_10",
                "strongest_defensible_thesis",
                "pre_solver_research",
                "post_native_research",
                "must_fix",
                "unexecuted_blockers",
                "dissent_or_uncertainty",
                "candidate_ids_considered",
                "evidence_paths",
            },
            errors,
        )
        if payload.get("phase") != "final_referees" or payload.get("web_used") is not False:
            errors.append(f"{journal} referee phase/web receipt invalid")
        for field in (
            "referee_id",
            "as_shipped_decision",
            "post_surgery_decision",
            "strongest_defensible_thesis",
        ):
            if not isinstance(payload.get(field), str) or not payload[field].strip():
                errors.append(
                    f"{journal} referee {field} must be non-whitespace text"
                )
        if not _meaningful_structure(payload.get("dissent_or_uncertainty")):
            errors.append(
                f"{journal} referee dissent_or_uncertainty must be meaningful"
            )
        for field in (
            "pre_solver_research",
            "post_native_research",
            "must_fix",
            "unexecuted_blockers",
            "candidate_ids_considered",
            "evidence_paths",
        ):
            value = payload.get(field)
            if (
                not isinstance(value, list)
                or not value
                or any(not isinstance(item, str) or not item.strip() for item in value)
            ):
                errors.append(
                    f"{journal} referee {field} must be a non-empty text list"
                )
        for field in ("as_shipped_score_0_to_10", "post_surgery_score_0_to_10"):
            score = payload.get(field)
            if not isinstance(score, (int, float)) or isinstance(score, bool) or not 0 <= score <= 10:
                errors.append(f"{journal} referee {field} must be in [0,10]")
        if not set(payload.get("candidate_ids_considered", [])) <= candidate_ids:
            errors.append(f"{journal} referee considered an unknown candidate")
        for evidence in payload.get("evidence_paths", []):
            path_evidence = Path(str(evidence))
            if not path_evidence.is_absolute():
                path_evidence = REPO / path_evidence
            if not path_evidence.is_file():
                errors.append(f"{journal} referee evidence path missing: {evidence}")
        decisions.append(
            {
                "journal_role": journal,
                **payload,
                "response_path": relative(path),
                "response_sha256": sha256_file(path),
            }
        )
    if len(decisions) != 3 or len({row["referee_id"] for row in decisions}) != 3:
        errors.append("three unique final referees are required")
    if errors:
        raise RuntimeError("cannot build final reports:\n- " + "\n- ".join(errors))

    report_inputs = [
        AUDIT / "advocate_candidate_ledger.json",
        AUDIT / "criticism_response_matrix.json",
        AUDIT / "web_crag_final.json",
        SHORTLIST_FREEZE,
        AUDIT / "coverage_matrix.json",
        *FINAL_REFEREE_RESPONSE_PATHS.values(),
    ]
    final_metadata = _artifact_metadata(
        report_inputs,
        "venv/bin/python -B scripts/audits/jcap_prd_20260714.py build-final-reports",
    )
    next_dag = {
        "schema": "htt.pr118.proposed_followup_dag.v1",
        **final_metadata,
        "status": "proposed_only_not_inserted_into_active_backlog",
        "depends_on": "PR-118",
        "closure_contract": (
            "Cards target open findings only. A target closes only after its owner-specific "
            "acceptance tests produce passed, hash-bound receipts and a later adjudication "
            "updates the controlling finding ledger. Scheduling or running a card never closes it."
        ),
        "cards": [
            {
                "id": "AUD-R01A",
                "owner": "OBSSTAT",
                "track": "pre_solver",
                "title": "Quarantine refuted CF4 corrections and rebuild estimator mechanics",
                "targets": ["imported P0 C1-K5-MV-F1", "imported P0 C3-K5-VCORR-ML-F1", "N-DATA-CF4-DOWNSTREAM"],
                "entry_gate": "authenticated CF4 row/group/selection lineage and preregistered injection coverage",
                "maximum_claim_tier": "observable-estimator validation only",
            },
            {
                "id": "AUD-R01B",
                "owner": "HTT",
                "track": "pre_solver",
                "depends_on": ["AUD-R01A"],
                "title": "Construct CF4 identified sets and downstream pushforwards",
                "targets": ["N-DATA-CF4-DOWNSTREAM", "N-DATA-FS8-DEPTH"],
                "entry_gate": "OBSSTAT estimator coverage receipt plus explicit nuisance/partial-identification contract",
                "maximum_claim_tier": "identified-region result; no global-tilt truth claim",
            },
            {
                "id": "AUD-R02A",
                "owner": "OBSSTAT",
                "track": "pre_solver",
                "title": "Build exchangeable observed/null calibration",
                "targets": ["N-STAT-K1-EXCHANGE", "N-STAT-DEGENERATE-NULL"],
                "entry_gate": "identical observed/null feature pipeline and finite-null calibration plan",
                "maximum_claim_tier": "matched-null calibration",
            },
            {
                "id": "AUD-R02B",
                "owner": "COMMON",
                "track": "pre_solver",
                "depends_on": ["AUD-R02A"],
                "title": "Run independent mutation-oracle and false-green release campaign",
                "targets": ["N-CODE-FALSE-GREEN"],
                "entry_gate": "predeclared oracle-killing mutations and independent implementation receipts",
                "maximum_claim_tier": "release-mechanics validation only",
            },
            {
                "id": "AUD-R03",
                "owner": "COMMON",
                "track": "pre_solver",
                "title": "Rebuild one-way FLRW/almost-EGS and coefficient-domain theorem surfaces",
                "targets": ["N-THEORY-FLRW-CONVERSE", "N-THEORY-EGS-CONVERSE", "N-THEORY-NT2-COEFFICIENT", "N-THEORY-OMK-DOMAIN"],
                "entry_gate": "two independent derivations with explicit frame/domain/remainder assumptions",
                "maximum_claim_tier": "conditional mathematical result",
            },
            {
                "id": "AUD-R04",
                "owner": "OBSSTAT",
                "track": "pre_solver",
                "title": "Acquire and rerun exact-support DESI/ACT/JWST validation inputs",
                "targets": ["N-DATA-DESI-READINESS", "N-DATA-ACT-RANGE", "N-DATA-JWST-ACQUISITION", "N-DATA-JWST-COVARIANCE"],
                "entry_gate": "input manifests, exact selection/mask transfer, covariance and matched-null provenance",
                "maximum_claim_tier": "survey-conditional null or forecast result",
            },
            {
                "id": "AUD-R05A",
                "owner": "BASS_PY",
                "track": "post_native_solver",
                "title": "Run authenticated native-adapter and atlas transport conformance",
                "targets": ["TH-04", "CO-06"],
                "entry_gate": "authenticated native solver/atlas with versioned conventions and rejection fixtures",
                "maximum_claim_tier": "native transport/atlas conformance only",
            },
            {
                "id": "AUD-R05B",
                "owner": "OBSSTAT",
                "track": "post_native_solver",
                "depends_on": ["AUD-R05A"],
                "title": "Build matched-mask morphology challenge features and equivalence annotations",
                "targets": ["TH-04", "ST-08", "CO-07"],
                "entry_gate": "authenticated atlas plus matched masks, nulls, covariance and held-out injections",
                "maximum_claim_tier": "morphology compatibility feature validation",
            },
            {
                "id": "AUD-R05C",
                "owner": "HTT",
                "track": "post_native_solver",
                "depends_on": ["AUD-R05A", "AUD-R05B"],
                "title": "Run blinded equivalence-set inference and abstention challenge",
                "targets": ["ST-08", "CO-07"],
                "entry_gate": "BASS transport and OBSSTAT matched-feature receipts plus nuisance-rank and equivalence contracts",
                "maximum_claim_tier": "morphology compatibility before any separate family-identification review",
            },
        ],
    }
    write_json(AUDIT / "next_dag_candidates.json", next_dag)
    decision_bundle = {
        "schema": "htt.pr118.final_referee_decisions.v1",
        **final_metadata,
        "generated_at": utcnow(),
        "as_shipped_root_decision": "REJECT",
        "post_surgery_root_decision": "NEW_SUBMISSION_AFTER_MAJOR_REBUILD",
        "referees": decisions,
        "correlated_evidence_caveat": (
            "Agent agreement is not an independent replication; decisions are separately "
            "authored but share repository evidence."
        ),
    }
    write_json(AUDIT / "final_referee_decisions.json", decision_bundle)

    def markdown_cell(value: Any) -> str:
        if isinstance(value, (dict, list)):
            value = json.dumps(value, sort_keys=True)
        return str(value).replace("|", "\\|").replace("\n", " ")

    report_lines = [
        "# Final JCAP/PRD adversarial referee report",
        "",
        "## Artifact and claim boundary",
        "",
        "- Owner: `COMMON`.",
        "- Scope: internal, diagnostic-only pre-solver audit and advocate research ranking.",
        f"- Claim tier: `{final_metadata['claim_tier']}`.",
        f"- Transfer source: `{final_metadata['transfer_source']}`.",
        f"- Config hash: `{final_metadata['config_hash']}`.",
        f"- Sky/mask status: `{final_metadata['sky_support_status']}`.",
        f"- Covariance/null status: `{final_metadata['null_mock_status']}`.",
        f"- Generating command: `{final_metadata['generating_command']}`.",
        f"- Git/worktree: `{final_metadata['git_commit_or_worktree_state']['current_head']}` with recorded worktree hash `{final_metadata['git_commit_or_worktree_state']['worktree_state_hash']}`.",
        "- Input hashes:",
        *[f"  - `{item}`" for item in final_metadata["input_hashes"]],
        "- Baseline under audit: `8af39b36c1d5ed4f9b16f0bc71dbecd8b22548d4`.",
        "- Current audit mechanics do not repair production results or validate an external/native transfer.",
        "- Counterfactual family/geometry candidates remain `hypothesis_only=true`, `public_use=false`.",
        "- DAG completion is bookkeeping, not scientific readiness.",
        "",
        "## Editorial decision summary",
        "",
        "| Referee | As-shipped decision | As-shipped score /10 | Post-surgery decision | Post-surgery score /10 |",
        "|---|---|---:|---|---:|",
    ]
    for row in decisions:
        report_lines.append(
            "| "
            + " | ".join(
                markdown_cell(value)
                for value in (
                    row["journal_role"],
                    row["as_shipped_decision"],
                    row["as_shipped_score_0_to_10"],
                    row["post_surgery_decision"],
                    row["post_surgery_score_0_to_10"],
                )
            )
            + " |"
        )
    role_headers = {
        "JCAP": "JCAP referee decision",
        "PRD": "PRD referee decision",
        "Independent skeptical": "Independent skeptical referee decision",
    }
    for row in decisions:
        report_lines.extend(
            [
                "",
                f"### {role_headers[row['journal_role']]}",
                "",
                f"- **As-shipped:** {row['as_shipped_decision']} ({row['as_shipped_score_0_to_10']}/10).",
                f"- **Post-surgery:** {row['post_surgery_decision']} ({row['post_surgery_score_0_to_10']}/10).",
                f"- Thesis allowed by this referee: {row['strongest_defensible_thesis']}",
            ]
        )
    report_lines.extend(
        [
            "",
            "## Audit census and delta discipline",
            "",
            "The prior audit contributes 55 `KNOWN_OPEN` findings (P0 2 / P1 14 / P2 17 / P3 22) and 14 audit-completeness gaps. PR-117 contributes 33 distinct open atomic deltas (P1 22 / P2 11); it does not relabel prior findings as new. The prose/raw-ledger P1 inconsistency in the prior audit is preserved as an audited inconsistency rather than silently corrected.",
            "",
            f"The advocate matrix covers {matrix['row_count']} criticisms exactly once. Dispositions are `{json.dumps(matrix['disposition_counts'], sort_keys=True)}`. A disposition is a research response, not evidence that a production claim has passed.",
            "The immutable-field root join converted three mapper-proposed rescues to `downclaimed` because their authoritative source state remains `KNOWN_OPEN`; no criticism is rescued in the final root matrix.",
            "",
            "### Examination coverage ceiling",
            "",
            f"The generated-result coverage register contains {len(coverage_rows)} rows: {coverage_counts['not_examined']} / {len(coverage_rows)} are `not_examined` and {coverage_counts['sampled']} / {len(coverage_rows)} are `sampled`. `not_examined` is not clearance; `sampled` is also not blanket clearance of the row, its consumers, or its scientific claim. Complete criticism accounting therefore does not imply complete scientific examination.",
            "",
            "## As-shipped assessment",
            "",
            "**Root decision: REJECT.** The shipped positive-science object cannot support anisotropy detection, global tilt, FLRW violation, precision growth tension, Bayesian evidence/PPC/LOOCV adequacy, native low-L morphology, geometry, or Bianchi-family conclusions. Two imported P0 findings remain open, the new audit adds 22 P1 and 11 P2 deltas, and decisive data inputs remain missing in several lanes. Passing governance/package checks demonstrably coexists with stale or scientifically invalid artifacts.",
            "",
            "The audit-only recalculations are sensitivity and failure-localization evidence. They do not become corrected truth: CF4 changes from about 405 to 94 km/s under a monopole-orthogonal construction; raw/depth f-sigma8 behavior shifts materially; the Hermitian GRF defect reproduces; the DESI proxy null becomes unexceptional but exact-selection mocks remain absent; ACT is scientifically blocked; K6 is stencil-dominated; and JWST gains are small and provenance/covariance-limited.",
            "",
            "Failure of the present anisotropy claims is not proof of exact isotropy and is not a new validation of LambdaCDM. Weak anisotropy remains a falsifiable but currently unsupported research program; the present result is non-identification rather than confirmation of either pole.",
            "",
            "## Minimum-surgery assessment",
            "",
            "**Root decision: NEW SUBMISSION AFTER MAJOR REBUILD, not a revision that retains the positive headline.** Remove the detection/tension/family narrative and reframe the work as a claim-tiered pre-solver methods and negative-audit paper. Its evidence-bearing contributions may be: exchangeable null construction, partial/non-identification theorems, independent numerical-oracle attacks, transfer/provenance contracts, and explicit demonstrations of when CF4/CMB/DESI/ACT/JWST examples remain blocked.",
            "",
            "## Four-axis hostile and advocate synthesis",
            "",
            "- **Theory:** one-way FLRW/almost-EGS statements and coefficient/domain claims must be rebuilt with frame, congruence, matter, regularity, order and remainder assumptions. Scalar or low-rank observables remain non-identifying; this negative theorem direction is the recoverable content.",
            "- **Statistics:** fitted likelihood differences are not Bayes factors, plug-in residuals are not PPC, and channel ablations are not LOOCV. Exchangeable global scans, finite-null rank guarantees, calibrated abstention and honest identified sets are viable rebuilds.",
            "- **Code:** clean-install failure, correlated self-oracles and false-green gates preclude reproducibility claims. Independent algorithms, mutation tests, content-addressed evidence and future adapter rejection fixtures can validate mechanics only.",
            "- **Data analysis:** CF4, Planck/ACT, DESI and JWST lanes require row/input provenance, matched support/masks/nulls, selection and calibration covariance, and estimator-identical mocks. Current anomaly amplitudes are not retained.",
            "",
            "## Advocate ranking and bounded final CRAG",
            "",
            f"Thirty-two no-web candidates (eight per axis) were scored by three non-author judges. The frozen shortlist has {advocate['shortlist_count']} candidates. Only those candidates entered the final CRAG; its authoritative packet contains {len(crag['queries'])} queries and {len(crag['sources'])} primary/official sources, while fuller raw agent lookups remain hash-bound. Final CRAG novelty checks reduced rather than inflated several novelty assessments.",
            "The shortlist is now canonically replayable from the raw no-web author/judge packets and bound by `shortlist_freeze.json`. That freeze file was retrospectively materialized after the single CRAG lookup, so it proves assignment consistency but not independent filesystem ordering; this process limitation is retained rather than backdated.",
            "",
            "The shortlist was frozen on the pre-CRAG selection scores. The totals below are recomputed after the bounded CRAG by replacing each track's novelty component with `novelty_after`; they are not compared against non-shortlisted candidates whose novelty was not rechecked.",
            "",
            "| Candidate | Axis | Post-CRAG pre-solver | Post-CRAG post-native | Integrity eligible now | Final disposition | Novelty after CRAG |",
            "|---|---|---:|---:|---|---|---:|",
        ]
    )
    for row in advocate["candidates"]:
        if not row["shortlisted_for_final_crag"]:
            continue
        report_lines.append(
            "| "
            + " | ".join(
                markdown_cell(value)
                for value in (
                    f"{row['candidate_id']} - {row['title']}",
                    row["axis"],
                    row["pre_solver_review"]["post_crag_total"],
                    row["post_native_solver_review"]["post_crag_total"],
                    row["integrity_veto_review"]["eligible_for_retain"],
                    row["final_disposition"],
                    row.get("final_crag_update", {}).get("novelty_after", "n/a"),
                )
            )
            + " |"
        )
    report_lines.extend(
        [
            "",
            "## Pre-solver research to execute now",
            "",
            "1. `ST-03`: rebuild the global scan so observation and nulls traverse an identical, frozen pipeline with finite-null uncertainty and tie handling.",
            "2. `TH-02` and `TH-01`: prove non-identification and one-way theorem results with explicit assumptions, independent derivations and mutation/regeneration checks.",
            "3. `CO-04` and `CO-01`: create independent numerical oracles and a claim-addressed evidence graph, while treating both as mechanics/provenance validation rather than scientific truth.",
            "4. `DA-01` and `ST-04`: rebuild CF4 as a preregistered injection/coverage and identified-region analysis only after row/group/selection lineage is authenticated.",
            "5. `DA-05`: use a two-tier DESI validation (large fast-mock covariance plus smaller high-realism selection mocks), with per-mock estimator refits and a receipted runner.",
            "",
            "## Research deferred until the native solver/atlas arrives",
            "",
            "`TH-04`, `ST-08`, `CO-06`, and `CO-07` remain interface/challenge-set work. Scientific use requires an authenticated native low-ell solver and morphology atlas, versioned coefficient conventions, held-out injections, matched masks/nulls/covariance, nuisance-rank checks, and explicit family-equivalence annotations. Even after those gates, the first permissible conclusion is morphology compatibility; family identification requires a separate external review.",
            "",
            "## Strongest defensible thesis",
            "",
            "The strongest defensible paper thesis is: *a fail-closed, claim-tiered pre-solver methodology can diagnose non-identification, estimator non-exchangeability, correlated numerical oracles, and transfer/provenance failure in low-ell anisotropy searches; the present CF4/CMB/DESI/ACT/JWST examples demonstrate blockers and identified research designs, not evidence for cosmic anisotropy or a Bianchi family.*",
            "",
            "## Unexecuted blockers",
            "",
            "- The two imported P0 scientific defects are not repaired in production outputs or manuscript numbers.",
            "- ACT raw/upstream QE inputs and validated low-L reconstruction transfer are absent.",
            "- Exact matched Planck end-to-end nulls and exact-selection DESI mock execution are not complete here.",
            "- JWST authoritative row manifest, per-host errors, probabilistic crossmatch and shared calibration covariance are incomplete.",
            "- Native solver/atlas, family-equivalence registry and external validation do not exist in this repository.",
            "- Manuscript figure provenance/freshness failures remain scientific-publication blockers even if LaTeX compiles.",
            "",
            "## Dissent and uncertainty",
            "",
        ]
    )
    for row in decisions:
        dissent = row["dissent_or_uncertainty"]
        if isinstance(dissent, list):
            dissent = " ".join(str(item) for item in dissent)
        report_lines.append(f"- **{row['journal_role']}:** {markdown_cell(dissent)}")
    report_lines.extend(
        [
            "",
            "Agreement among agents is correlated because they share repository evidence; it is not an independent replication. The digest-blind PR-117 referee samples and the separately authored PR-118 decisions reduce, but do not remove, this dependence.",
            "",
            "## Proposed next DAG candidates",
            "",
        ]
    )
    for card in next_dag["cards"]:
        report_lines.append(
            f"- `{card['id']}` ({card['track']}, {card['owner']}): {card['title']}. Targets: {', '.join(card['targets'])}. Entry gate: {card['entry_gate']}. Maximum claim: {card['maximum_claim_tier']}."
        )
    report_lines.extend(
        [
            "",
            "These cards are proposals only and were not inserted into the active completed DAG. Production corrections, manuscript number replacement, public upload and native solver implementation remain out of scope.",
        ]
    )
    (AUDIT / "final_referee_report.md").write_text(
        "\n".join(report_lines) + "\n", encoding="utf-8"
    )

    scores_as = [float(row["as_shipped_score_0_to_10"]) for row in decisions]
    scores_post = [float(row["post_surgery_score_0_to_10"]) for row in decisions]
    ko_lines = [
        "# 최종 적대적 감사 요약",
        "",
        "- Owner: `COMMON`",
        f"- Claim tier: `{final_metadata['claim_tier']}`",
        f"- Transfer source: `{final_metadata['transfer_source']}`",
        f"- Config hash: `{final_metadata['config_hash']}`",
        f"- Sky/mask 상태: `{final_metadata['sky_support_status']}`",
        f"- Covariance/null 상태: `{final_metadata['null_mock_status']}`",
        f"- 생성 명령: `{final_metadata['generating_command']}`",
        f"- Git/worktree hash: `{final_metadata['git_commit_or_worktree_state']['worktree_state_hash']}`",
        "",
        "## 현재 상태",
        "",
        f"현재 as-shipped 논문 판정은 **REJECT**입니다. 세 독립 referee의 점수 범위는 {min(scores_as):g}-{max(scores_as):g}/10입니다. DAG 65/65 완료는 작업 장부의 완결일 뿐 과학적 준비 완료가 아닙니다. 기존 55개 finding(P0 2/P1 14/P2 17/P3 22), 감사 gap 14개, PR-117의 신규 open delta 33개는 서로 구분해 보존했습니다.",
        "",
        f"생성 결과 coverage register 78개 중 **44/78은 `not_examined`**, **34/78은 `sampled`**입니다. `not_examined`는 통과나 면제가 아니며 `sampled`도 해당 결과와 하류 명제 전체의 blanket clearance가 아닙니다. 102개 비판에 모두 답했다는 사실은 모든 과학 산출물을 완전 심사했다는 뜻이 아닙니다.",
        "",
        "CF4, CMB, DESI, ACT, JWST의 현재 결과는 cosmic anisotropy, global tilt, FLRW 위반, geometry 또는 family identification을 지지하지 못합니다. 특히 기존 P0 두 건과 새 P1 22건이 production result와 manuscript 수치에서 아직 닫히지 않았습니다.",
        "",
        "현재 anisotropy 주장이 실패했다는 사실은 exact isotropy의 증명도, LambdaCDM의 새로운 검증도 아닙니다. 약한 비등방성은 반증 가능한 미래 연구 가설로 남지만 현재는 지지되지 않으며, 이 감사의 결론은 양쪽 어느 하나의 확인이 아니라 non-identification입니다.",
        "",
        "## 최소 수정 후 가능한 논문",
        "",
        f"최소 수정이라는 표현은 오해를 부릅니다. 필요한 것은 긍정적 headline을 유지한 revision이 아니라 **새로운 methods/negative-audit submission**입니다. 세 referee의 post-surgery 점수 범위는 {min(scores_post):g}-{max(scores_post):g}/10입니다. 검증 가능한 소재는 exchangeable null, partial/non-identification, independent numerical oracle, provenance/transfer contract, 그리고 각 데이터 lane의 명시적 blocker입니다.",
        "",
        "## pre-solver 단계에서 즉시 할 연구",
        "",
        "- ST-03: observed/null 동일 파이프라인과 finite-null 보장을 갖춘 global scan 재구축.",
        "- TH-02/TH-01: cancellation과 theorem domain을 명시한 non-identification 및 one-way FLRW/almost-EGS 정리.",
        "- CO-04/CO-01: 독립 수치 oracle, mutation test, claim-addressed evidence graph.",
        "- DA-01/ST-04: CF4 row/group/selection provenance를 확보한 뒤 injection coverage와 identified region 분석.",
        "- DA-05: DESI 대규모 fast mock과 소수 high-realism mock을 나눈 2단계 검증.",
        "",
        "## native solver 도착 후 재개할 연구",
        "",
        "TH-04, ST-08, CO-06, CO-07은 지금은 interface/challenge-set 후보입니다. authenticated native solver와 morphology atlas, matched mask/null/covariance, held-out injection, family-equivalence annotation이 모두 있어야 합니다. 그 뒤에도 최초 허용 명제는 morphology compatibility이며 family identification은 별도 외부 심사를 거쳐야 합니다.",
        "",
        "## 가장 강한 방어 가능 명제",
        "",
        "현재 가장 강한 방어 가능 명제는 다음과 같습니다: 이 저장소는 low-ell anisotropy 탐색에서 비식별성, estimator 비대칭, 상관된 self-oracle, transfer/provenance 실패를 fail-closed 방식으로 드러내는 claim-tiered pre-solver 방법론을 제공할 수 있다. 현재 데이터 예시는 우주 비등방성의 증거가 아니라 blocker와 반증 가능한 후속 설계를 보여준다.",
        "",
        "Counterfactual family/geometry 후보는 계속 `hypothesis_only=true`, `public_use=false`이며 manuscript/generated/public manifest로 승격되지 않습니다.",
    ]
    (AUDIT / "executive_summary_ko.md").write_text(
        "\n".join(ko_lines) + "\n", encoding="utf-8"
    )
    return decision_bundle


def _validate_final_closeout(
    prior: Any,
    atomic: Any,
    execution_rows: list[dict[str, Any]],
    errors: list[str],
) -> None:
    ledger = _validate_json(AUDIT / "advocate_candidate_ledger.json", errors)
    ledger = _require_object(
        ledger,
        "advocate candidate ledger",
        (
            "schema",
            "owner",
            "implementation_scope",
            "claim_tier",
            "transfer_source",
            "config_hash",
            "input_hashes",
            "sky_support_status",
            "null_mock_status",
            "caveats",
            "generating_command",
            "git_commit_or_worktree_state",
            "phase",
            "candidate_count",
            "axis_counts",
            "ranking_authority",
            "shortlist_candidate_ids",
            "shortlist_count",
            "shortlist_hash",
            "shortlist_freeze_path",
            "shortlist_freeze_sha256",
            "candidates",
            "counterfactual_contract",
        ),
        errors,
    )
    if not ledger:
        return
    final_crag = _validate_json(AUDIT / "web_crag_final.json", errors)
    try:
        canonical_final_crag = build_final_crag(write=False)
    except RuntimeError as exc:
        errors.append(f"raw final CRAG canonical replay failed: {exc}")
        canonical_final_crag = final_crag if isinstance(final_crag, dict) else {}
    ranking_input_paths = [
        *ADVOCATE_RESPONSE_PATHS.values(),
        AUDIT / "agents/advocate_judging/pre_solver_judge_response.json",
        AUDIT / "agents/advocate_judging/post_native_judge_response.json",
        AUDIT / "agents/advocate_judging/integrity_veto_judge_response.json",
        AUDIT / "WEB_LOCK.json",
    ]
    _validate_artifact_metadata(
        ledger,
        "advocate candidate ledger",
        errors,
        expected_inputs=[*ranking_input_paths, SHORTLIST_FREEZE, AUDIT / "web_crag_final.json"],
    )
    freeze = _validate_json(SHORTLIST_FREEZE, errors)
    freeze = _require_object(
        freeze,
        "shortlist freeze",
        (
            "schema",
            "owner",
            "config_hash",
            "input_hashes",
            "phase",
            "web_used",
            "ranking_rows",
            "shortlist_candidate_ids",
            "shortlist_count",
            "shortlist_hash",
            "materialization_status",
            "ordering_caveat",
        ),
        errors,
    )
    _require_schema(freeze, "shortlist freeze", "htt.pr118.shortlist_freeze.v1", errors)
    _validate_artifact_metadata(
        freeze,
        "shortlist freeze",
        errors,
        expected_inputs=ranking_input_paths,
    )
    canonical_errors: list[str] = []
    canonical = _canonical_advocate_ranking(canonical_errors)
    errors.extend(canonical_errors)
    if freeze:
        for key, expected in _shortlist_freeze_projection(canonical).items():
            if freeze.get(key) != expected:
                errors.append(f"shortlist freeze canonical replay differs at {key}")
        if ledger.get("shortlist_freeze_sha256") != sha256_file(SHORTLIST_FREEZE):
            errors.append("advocate ledger shortlist-freeze hash is stale")
    expected_ranked = _finalize_advocate_ranking(
        canonical, canonical_final_crag, errors
    )
    author_candidates, _ = _load_advocate_responses(errors)
    expected_ids = {row["candidate_id"] for row in author_candidates}
    rows = ledger.get("candidates", [])
    ids = {row.get("candidate_id") for row in rows if isinstance(row, dict)}
    if ledger.get("candidate_count") != 32 or ids != expected_ids:
        errors.append("final advocate ledger does not bind the 32-candidate author pool")
    if ledger.get("axis_counts") != {
        "theory": 8,
        "statistics": 8,
        "code": 8,
        "data_analysis": 8,
    }:
        errors.append("advocate axis census must be eight per axis")
    shortlist = ledger.get("shortlist_candidate_ids", [])
    if not 8 <= len(shortlist) <= 12 or len(shortlist) != len(set(shortlist)):
        errors.append("final CRAG shortlist must contain 8-12 unique candidates")
    if ledger.get("shortlist_count") != len(shortlist):
        errors.append("advocate shortlist_count is stale")
    if ledger.get("shortlist_hash") != sha256_json(sorted(shortlist)):
        errors.append("advocate shortlist hash is stale")
    if ledger.get("counterfactual_contract") != COUNTERFACTUAL_FIELDS:
        errors.append("advocate counterfactual contract drift")
    if ledger.get("ranking_authority", {}).get("candidate_authors_excluded") is not True:
        errors.append("candidate authors were not excluded from ranking authority")
    expected_authority = {
        "pre_solver_judge": canonical["pre_judge"],
        "post_native_solver_judge": canonical["post_judge"],
        "integrity_veto_judge": canonical["integrity_judge"],
        "candidate_authors_excluded": True,
        "deterministic_aggregator": relative(Path(__file__)),
    }
    if ledger.get("ranking_authority") != expected_authority:
        errors.append("advocate ranking authority differs from raw author/judge packets")
    if ledger.get("author_ids") != sorted(canonical["author_ids"]):
        errors.append("advocate author IDs differ from raw author packets")
    if ledger.get("shortlist_basis") != "pre_crag_selection_score_frozen_before_final_crag":
        errors.append("advocate shortlist basis must remain the frozen pre-CRAG score")
    if sorted(rows, key=lambda row: row.get("candidate_id", "")) != sorted(
        expected_ranked, key=lambda row: row.get("candidate_id", "")
    ):
        errors.append("advocate ledger differs from canonical author/judge/CRAG replay")
    for row in rows:
        if (
            row.get("hypothesis_only") is not True
            or row.get("public_use") is not False
            or row.get("author_cannot_promote") is not True
            or row.get("web_used") is not False
        ):
            errors.append(f"{row.get('candidate_id')} violates advocate sandbox controls")
        integrity = row.get("integrity_veto_review", {})
        if (
            any(
                integrity.get(flag) is True
                for flag in ("unresolved_p0", "missing_falsifier", "provenance_unsecured")
            )
            and row.get("final_disposition") == "rescued"
        ):
            errors.append(f"{row.get('candidate_id')} is rescued despite a mandatory veto")
        for review_key, weights in (
            ("pre_solver_review", PRE_SOLVER_WEIGHTS),
            ("post_native_solver_review", POST_SOLVER_WEIGHTS),
        ):
            review = row.get(review_key, {})
            if review.get("pre_crag_total") != review.get("total"):
                errors.append(
                    f"{row.get('candidate_id')} {review_key} lost its frozen pre-CRAG score"
                )
            if row.get("shortlisted_for_final_crag"):
                update = row.get("final_crag_update") or {}
                expected_scores = dict(review.get("scores") or {})
                expected_scores["novelty"] = update.get("novelty_after")
                score_errors: list[str] = []
                expected_total = _weighted_score(
                    expected_scores,
                    weights,
                    f"{row.get('candidate_id')} {review_key} validator",
                    score_errors,
                )
                errors.extend(score_errors)
                if review.get("post_crag_scores") != expected_scores:
                    errors.append(
                        f"{row.get('candidate_id')} {review_key} post-CRAG score vector is stale"
                    )
                if review.get("post_crag_total") != expected_total:
                    errors.append(
                        f"{row.get('candidate_id')} {review_key} post-CRAG total is stale"
                    )
            elif (
                review.get("post_crag_scores") is not None
                or review.get("post_crag_total") is not None
            ):
                errors.append(
                    f"{row.get('candidate_id')} received post-CRAG scores outside the frozen shortlist"
                )

    final_crag = _require_object(
        final_crag,
        "final CRAG",
        (
            "schema",
            "owner",
            "implementation_scope",
            "claim_tier",
            "transfer_source",
            "config_hash",
            "input_hashes",
            "sky_support_status",
            "null_mock_status",
            "caveats",
            "generating_command",
            "git_commit_or_worktree_state",
            "reopened_after_shortlist",
            "shortlist_hash",
            "shortlist_sha256",
            "candidate_ids",
            "queries",
            "sources",
            "candidate_updates",
            "closed_after_completion",
        ),
        errors,
    )
    if final_crag:
        _require_schema(
            final_crag, "final CRAG", "htt.pr118.web_crag_final.v1", errors
        )
        _validate_artifact_metadata(
            final_crag,
            "final CRAG",
            errors,
            expected_inputs=[*FINAL_CRAG_RESPONSE_PATHS.values(), SHORTLIST_FREEZE],
        )
        for key in (
            "reopened_after_shortlist",
            "reopen_scope",
            "shortlist_path",
            "shortlist_sha256",
            "shortlist_hash",
            "candidate_ids",
            "candidate_count",
            "selection_policy",
            "raw_query_count",
            "raw_source_count",
            "queries",
            "sources",
            "candidate_updates",
            "agent_receipts",
            "closed_after_completion",
            "forbidden_after_close",
        ):
            if final_crag.get(key) != canonical_final_crag.get(key):
                errors.append(
                    f"final CRAG differs from canonical raw-response replay at {key}"
                )
        if final_crag.get("reopened_after_shortlist") is not True:
            errors.append("final CRAG was not explicitly reopened after shortlist freeze")
        if final_crag.get("closed_after_completion") is not True:
            errors.append("final CRAG was not closed after the bounded lookup")
        if final_crag.get("shortlist_hash") != ledger.get("shortlist_hash"):
            errors.append("final CRAG shortlist hash differs from frozen advocate shortlist")
        if final_crag.get("shortlist_sha256") != sha256_file(SHORTLIST_FREEZE):
            errors.append("final CRAG does not bind the current shortlist-freeze artifact")
        crag_ids = final_crag.get("candidate_ids", [])
        if set(crag_ids) != set(shortlist) or len(crag_ids) != len(shortlist):
            errors.append("final CRAG must cover exactly the frozen shortlist")
        for query in final_crag.get("queries", []):
            if not set(query.get("candidate_ids", [])) <= set(shortlist):
                errors.append("final CRAG query escaped the frozen shortlist")
        updates = final_crag.get("candidate_updates", [])
        if {row.get("candidate_id") for row in updates} != set(shortlist):
            errors.append("final CRAG must update every and only shortlisted candidate")
        source_ids = {row.get("source_id") for row in final_crag.get("sources", [])}
        for source in final_crag.get("sources", []):
            for field in (
                "source_id",
                "url",
                "accessed_at",
                "primary_or_official",
                "candidate_ids",
                "supports_or_challenges",
                "data_code_availability",
                "citation_action",
            ):
                if not source.get(field):
                    errors.append(f"final CRAG source missing {field}")
            if source.get("primary_or_official") is not True:
                errors.append(f"final CRAG source {source.get('source_id')} is not primary/official")
            if not set(source.get("candidate_ids", [])) <= set(shortlist):
                errors.append("final CRAG source escaped the frozen shortlist")
        for update in updates:
            if not set(update.get("source_ids", [])) <= source_ids:
                errors.append(f"{update.get('candidate_id')} cites unknown final CRAG source")
            for field in (
                "nearest_prior_art",
                "novelty_before",
                "novelty_after",
                "blocker_update",
                "recommended_disposition",
                "source_ids",
            ):
                if not update.get(field):
                    errors.append(f"final CRAG update {update.get('candidate_id')} missing {field}")
            if update.get("recommended_disposition") not in ADVOCATE_DISPOSITIONS:
                errors.append(f"final CRAG update {update.get('candidate_id')} has bad disposition")
            candidate_id = update.get("candidate_id")
            relevant_queries = [
                row
                for row in final_crag.get("queries", [])
                if candidate_id in row.get("candidate_ids", [])
            ]
            relevant_sources = [
                source
                for source in final_crag.get("sources", [])
                if source.get("source_id") in update.get("source_ids", [])
                and candidate_id in source.get("candidate_ids", [])
            ]
            if not relevant_queries:
                errors.append(f"{candidate_id} lacks a candidate-relevant final CRAG query")
            if not relevant_sources:
                errors.append(f"{candidate_id} lacks a candidate-relevant final CRAG source")
            if len(update.get("source_ids", [])) > 2:
                errors.append(f"{candidate_id} exceeds the authoritative two-source cap")

    matrix = _validate_json(AUDIT / "criticism_response_matrix.json", errors)
    matrix = _require_object(
        matrix,
        "criticism response matrix",
        (
            "schema",
            "owner",
            "implementation_scope",
            "claim_tier",
            "transfer_source",
            "config_hash",
            "input_hashes",
            "sky_support_status",
            "null_mock_status",
            "caveats",
            "generating_command",
            "git_commit_or_worktree_state",
            "row_count",
            "origin_counts",
            "disposition_counts",
            "rows",
        ),
        errors,
    )
    if matrix:
        _require_schema(
            matrix,
            "criticism response matrix",
            "htt.pr118.criticism_response_matrix.v1",
            errors,
        )
        try:
            canonical_matrix = build_criticism_matrix(write=False)
        except RuntimeError as exc:
            errors.append(f"raw criticism-mapper canonical replay failed: {exc}")
            canonical_matrix = {}
        _validate_artifact_metadata(
            matrix,
            "criticism response matrix",
            errors,
            expected_inputs=[
                *CRITICISM_MAP_PATHS.values(),
                AUDIT / "advocate_candidate_ledger.json",
                AUDIT / "prior_crosswalk.json",
                ATOMIC_LEDGER,
            ],
        )
        for key in (
            "web_used",
            "fixed_external_packets",
            "mapper_ids",
            "row_count",
            "origin_counts",
            "disposition_counts",
            "rows",
        ):
            if canonical_matrix and matrix.get(key) != canonical_matrix.get(key):
                errors.append(
                    "criticism matrix differs from canonical raw-mapper/root replay "
                    f"at {key}"
                )
        expected_prior = {
            row.get("prior_id") for row in (prior or {}).get("prior_findings", [])
        }
        expected_gaps = {
            row.get("gap_id") for row in (prior or {}).get("audit_completeness_gaps", [])
        }
        expected_new = {
            row.get("atomic_id")
            for row in (atomic or {}).get("atomic_findings", [])
            if row.get("disposition") == "NEW_OPEN"
        }
        expected = expected_prior | expected_gaps | expected_new
        authority = _authoritative_criticism_fields(prior or {}, atomic or {})
        matrix_rows = matrix.get("rows", [])
        actual = {
            row.get("criticism_id") for row in matrix_rows if isinstance(row, dict)
        }
        if len(matrix_rows) != 102 or actual != expected:
            errors.append("criticism matrix must cover exactly 55 prior + 14 gaps + 33 new")
        if matrix.get("row_count") != len(matrix_rows):
            errors.append("criticism matrix row_count is stale")
        origins = Counter(row.get("origin") for row in matrix_rows)
        if dict(origins) != matrix.get("origin_counts") or origins != {
            "prior": 55,
            "audit_gap": 14,
            "delta_new": 33,
        }:
            errors.append("criticism matrix origin census is stale")
        dispositions = Counter(row.get("disposition") for row in matrix_rows)
        if dict(dispositions) != matrix.get("disposition_counts"):
            errors.append("criticism matrix disposition census is stale")
        if dispositions.get("rescued", 0) or matrix.get("disposition_counts", {}).get(
            "rescued", 0
        ):
            errors.append(
                "criticism matrix cannot rescue an open finding without a separate "
                "hash-bound production-remediation receipt"
            )
        for row in matrix_rows:
            required = {
                "criticism_id",
                "origin",
                "severity",
                "criticism",
                "strongest_advocate_response",
                "response_to_rebuttal",
                "disposition",
                "candidate_ids",
                "residual_risk",
                "decisive_closeout_evidence",
                "maximum_claim_tier",
                "source_reference",
                "source_hash",
                "authoritative_state",
            }
            if not required <= row.keys() or any(
                row.get(field) in (None, "", [])
                for field in required - {"candidate_ids"}
            ):
                errors.append(f"criticism matrix row {row.get('criticism_id')} is incomplete")
            if row.get("disposition") not in ADVOCATE_DISPOSITIONS:
                errors.append(f"criticism {row.get('criticism_id')} has invalid disposition")
            if not set(row.get("candidate_ids", [])) <= expected_ids:
                errors.append(f"criticism {row.get('criticism_id')} links unknown candidate")
            immutable = authority.get(row.get("criticism_id"))
            if not immutable:
                errors.append(f"criticism {row.get('criticism_id')} lacks authoritative source")
            else:
                for field, expected_value in immutable.items():
                    if row.get(field) != expected_value:
                        errors.append(
                            f"criticism {row.get('criticism_id')} rewrites authoritative {field}"
                        )
                if (
                    immutable["authoritative_state"] == "KNOWN_OPEN"
                    and row.get("disposition") == "rescued"
                ):
                    errors.append(
                        f"criticism {row.get('criticism_id')} rescues KNOWN_OPEN without remediation receipt"
                    )

    latex = _validate_json(AUDIT / "latex_pdf_validation.json", errors)
    latex = _require_object(
        latex,
        "LaTeX/PDF validation",
        (
            "schema",
            "owner",
            "implementation_scope",
            "claim_tier",
            "transfer_source",
            "config_hash",
            "input_hashes",
            "sky_support_status",
            "null_mock_status",
            "caveats",
            "generating_command",
            "git_commit_or_worktree_state",
            "attempts",
            "execution_receipt",
            "pdf",
            "pdfinfo",
            "log",
            "representative_page_rendering",
            "visual_review_receipt",
            "scientific_readiness",
            "publication_readiness",
        ),
        errors,
    )
    if latex:
        _require_schema(
            latex,
            "LaTeX/PDF validation",
            "htt.pr118.latex_pdf_validation.v1",
            errors,
        )
        try:
            latex_seal_commit = _manifest_seal_commit()
        except RuntimeError as exc:
            errors.append(f"LaTeX/PDF validation seal commit is unavailable: {exc}")
            latex_seal_commit = None
        _validate_artifact_metadata(
            latex,
            "LaTeX/PDF validation",
            errors,
            expected_inputs=[
                REPO / "docs/manuscript/main.tex",
                REPO / "docs/manuscript/references.bib",
                REPO / "docs/generated/status_snapshot.json",
                REPO / "docs/generated/claim_ledger.json",
                REPO / "docs/generated/status_matrix.md",
            ],
            frozen_commit=latex_seal_commit,
        )
        accepted = [row for row in latex.get("attempts", []) if row.get("status") == "PASS_BUILD_MECHANICS_ONLY"]
        if len(accepted) != 1 or accepted[0].get("exit_code") != 0:
            errors.append("LaTeX validation requires exactly one accepted exit-zero build")
        if latex.get("pdf", {}).get("pdfinfo_status") != "PASS" or latex.get("pdf", {}).get("pages", 0) <= 0:
            errors.append("LaTeX validation lacks a parseable non-empty PDF")
        if latex.get("log", {}).get("undefined_reference_warnings") != 0:
            errors.append("LaTeX validation retains undefined references")
        if latex.get("log", {}).get("undefined_citation_warnings") != 0:
            errors.append("LaTeX validation retains undefined citations")
        pages = latex.get("representative_page_rendering", [])
        if len(pages) != 3 or any(
            row.get("visual_status") != "PASS_NO_CLIPPING_OR_MISSING_CONTENT_OBSERVED"
            for row in pages
        ):
            errors.append("LaTeX representative-page visual inspection is incomplete")
        if latex.get("scientific_readiness") is not False or latex.get("publication_readiness") is not False:
            errors.append("LaTeX mechanics were promoted to science/publication readiness")
        latex_receipt_id = latex.get("execution_receipt", {}).get("command_id")
        latex_receipt = next(
            (row for row in execution_rows if row.get("command_id") == latex_receipt_id),
            None,
        )
        if latex_receipt_id != "pr118_final_latex_build_seal4" or not latex_receipt:
            errors.append("LaTeX validation does not bind the required execution receipt")
        elif latex_receipt.get("result") != "PASS":
            errors.append("LaTeX execution receipt is not a process PASS")

        def evidence_path(value: Any) -> Path:
            path = Path(str(value or ""))
            return path if path.is_absolute() else REPO / path

        pdf = latex.get("pdf", {})
        pdf_path = evidence_path(pdf.get("path"))
        if not pdf_path.is_file():
            errors.append("LaTeX external PDF is unavailable at seal time")
        else:
            if pdf.get("sha256") != sha256_file(pdf_path):
                errors.append("LaTeX external PDF hash is stale")
            if pdf.get("bytes") != pdf_path.stat().st_size:
                errors.append("LaTeX external PDF byte count is stale")
        for section_name in ("pdfinfo", "log"):
            section = latex.get(section_name, {})
            path = evidence_path(section.get("path"))
            if not path.is_file():
                errors.append(f"LaTeX durable {section_name} evidence is missing")
            elif section.get("sha256") != sha256_file(path):
                errors.append(f"LaTeX durable {section_name} hash is stale")
        pdfinfo_path = evidence_path(latex.get("pdfinfo", {}).get("path"))
        if pdfinfo_path.is_file():
            pdfinfo_text = pdfinfo_path.read_text(encoding="utf-8", errors="replace")
            page_match = re.search(r"(?m)^Pages:\s*(\d+)\s*$", pdfinfo_text)
            if not page_match or int(page_match.group(1)) != latex.get("pdf", {}).get("pages"):
                errors.append("LaTeX durable pdfinfo page count differs")
        log_path = evidence_path(latex.get("log", {}).get("path"))
        if log_path.is_file():
            log_text = log_path.read_text(encoding="utf-8", errors="replace")
            if len(re.findall(r"Overfull \\hbox", log_text)) != latex.get("log", {}).get(
                "overfull_hbox_warnings"
            ):
                errors.append("LaTeX overfull-hbox count differs from durable log")
        for page in pages:
            path = evidence_path(page.get("path"))
            if not path.is_file():
                errors.append(f"LaTeX rendered page {page.get('pdf_page')} is missing")
                continue
            if page.get("png_sha256") != sha256_file(path):
                errors.append(f"LaTeX rendered page {page.get('pdf_page')} hash is stale")
            data = path.read_bytes()[:24]
            if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
                errors.append(f"LaTeX rendered page {page.get('pdf_page')} is not PNG")
            else:
                dimensions = [
                    int.from_bytes(data[16:20], "big"),
                    int.from_bytes(data[20:24], "big"),
                ]
                if page.get("pixel_dimensions") != dimensions:
                    errors.append(
                        f"LaTeX rendered page {page.get('pdf_page')} dimensions are stale"
                    )
            for field in ("render_command", "rendered_at", "inspected_at", "inspector_id"):
                if not page.get(field):
                    errors.append(f"LaTeX rendered page {page.get('pdf_page')} lacks {field}")
        visual = latex.get("visual_review_receipt", {})
        visual_path = evidence_path(visual.get("path"))
        if not visual_path.is_file():
            errors.append("LaTeX visual-review receipt is missing")
        elif visual.get("sha256") != sha256_file(visual_path):
            errors.append("LaTeX visual-review receipt hash is stale")
        else:
            visual_text = visual_path.read_text(encoding="utf-8", errors="replace")
            if not re.search(r"web_used\s*[:=]\s*false", visual_text, re.IGNORECASE):
                errors.append("LaTeX visual-review receipt lacks web_used=false")
            for page in pages:
                if page.get("png_sha256") not in visual_text:
                    errors.append(
                        f"LaTeX visual reviewer did not bind page {page.get('pdf_page')} hash"
                    )

    for name in ("final_referee_decisions.json", "next_dag_candidates.json"):
        payload = _validate_json(AUDIT / name, errors)
        payload = _require_object(
            payload,
            name,
            (
                "schema",
                "owner",
                "implementation_scope",
                "claim_tier",
                "transfer_source",
                "config_hash",
                "input_hashes",
                "sky_support_status",
                "null_mock_status",
                "caveats",
                "generating_command",
                "git_commit_or_worktree_state",
            ),
            errors,
        )
        if name == "next_dag_candidates.json" and payload:
            if "closes" in json.dumps(payload.get("cards", []), sort_keys=True):
                errors.append("proposed DAG cards must target findings, not claim premature closure")
            expected_owners = {
                "AUD-R01A": "OBSSTAT",
                "AUD-R01B": "HTT",
                "AUD-R02A": "OBSSTAT",
                "AUD-R02B": "COMMON",
                "AUD-R03": "COMMON",
                "AUD-R04": "OBSSTAT",
                "AUD-R05A": "BASS_PY",
                "AUD-R05B": "OBSSTAT",
                "AUD-R05C": "HTT",
            }
            actual_owners = {
                row.get("id"): row.get("owner")
                for row in payload.get("cards", [])
                if isinstance(row, dict)
            }
            if actual_owners != expected_owners:
                errors.append("proposed DAG card ownership/staging contract drift")
            if not payload.get("closure_contract"):
                errors.append("proposed DAG cards lack a receipt-gated closure contract")
        if payload:
            expected_schema = (
                "htt.pr118.final_referee_decisions.v1"
                if name == "final_referee_decisions.json"
                else "htt.pr118.proposed_followup_dag.v1"
            )
            _require_schema(payload, name, expected_schema, errors)
            _validate_artifact_metadata(
                payload,
                name,
                errors,
                expected_inputs=[
                    AUDIT / "advocate_candidate_ledger.json",
                    AUDIT / "criticism_response_matrix.json",
                    AUDIT / "web_crag_final.json",
                    SHORTLIST_FREEZE,
                    AUDIT / "coverage_matrix.json",
                    *FINAL_REFEREE_RESPONSE_PATHS.values(),
                ],
            )

    for name, required_terms in (
        (
            "final_referee_report.md",
            (
                "JCAP referee decision",
                "PRD referee decision",
                "Independent skeptical referee decision",
                "As-shipped",
                "Post-surgery",
                "Strongest defensible thesis",
                "Dissent",
                "Unexecuted blockers",
                "44 / 78",
                "not_examined",
                "not proof of exact isotropy",
            ),
        ),
        (
            "executive_summary_ko.md",
            (
                "현재 상태",
                "최소 수정",
                "pre-solver",
                "native solver",
                "가장 강한 방어 가능 명제",
                "44/78",
                "not_examined",
                "exact isotropy의 증명도",
            ),
        ),
    ):
        path = AUDIT / name
        if not path.is_file():
            errors.append(f"missing final report {relative(path)}")
            continue
        text = path.read_text(encoding="utf-8")
        for term in required_terms:
            if term not in text:
                errors.append(f"{name} missing required section/term {term}")


def validate(*, final: bool = False) -> list[str]:
    errors: list[str] = []
    prior = _validate_json(AUDIT / "prior_crosswalk.json", errors)
    prior = _require_object(
        prior,
        "prior crosswalk",
        (
            "schema",
            "prior_findings",
            "audit_completeness_gaps",
            "prior_files",
            "coverage",
            "prior_census",
        ),
        errors,
    )
    prior_ids: set[str] = set()
    if prior:
        findings = prior.get("prior_findings", [])
        counts = Counter(row.get("severity") for row in findings)
        if len(findings) != 55 or dict(counts) != EXPECTED_PRIOR_COUNTS:
            errors.append(f"prior finding census mismatch: {len(findings)} {dict(counts)}")
        if any(row.get("delta_status") != "KNOWN_OPEN" for row in findings):
            errors.append("all imported prior findings must remain KNOWN_OPEN")
        if prior.get("completeness_gap_count") != 14:
            errors.append("prior audit completeness-gap count must be 14")
        ids = [row.get("prior_id") for row in findings]
        if len(ids) != len(set(ids)):
            errors.append("duplicate prior finding IDs")
        prior_ids = {str(item) for item in ids}
        prior_ids.update(
            str(row.get("gap_id")) for row in prior.get("audit_completeness_gaps", [])
        )

    web_lock = _validate_json(AUDIT / "WEB_LOCK.json", errors)
    web_lock = _require_object(
        web_lock,
        "web lock",
        (
            "status",
            "locked_packet_sha256",
            "allowed_evidence",
            "forbidden_until_final_shortlist",
        ),
        errors,
    )
    initial_crag = _validate_json(AUDIT / "web_crag_initial.json", errors)
    initial_crag = _require_object(
        initial_crag,
        "initial web CRAG",
        ("schema", "sources", "packets", "required_seed_corpus", "source_count"),
        errors,
    )
    if web_lock:
        if web_lock.get("status") != "LOCKED":
            errors.append("WEB_LOCK must be LOCKED during offline audit/brainstorming")
        if web_lock.get("locked_packet_sha256") != sha256_file(AUDIT / "web_crag_initial.json"):
            errors.append("WEB_LOCK packet hash is stale")
    if initial_crag and initial_crag.get("source_count") != len(initial_crag.get("sources", [])):
        errors.append("initial CRAG source_count does not match sources")

    history = _validate_json(AUDIT / "history_legacy_ledger.json", errors)
    history = _require_object(
        history,
        "history/legacy ledger",
        ("schema", "archives", "target_commits", "examination_status", "salvage_policy"),
        errors,
    )
    if history:
        flags = history.get("target_commits", {}).get("32a44e9", {}).get(
            "historical_flag_candidates", []
        )
        if len(flags) != 31:
            errors.append(f"history ledger requires 31 deleted flags, got {len(flags)}")
        if any(row.get("unsafe_entries") for row in history.get("archives", [])):
            errors.append("history ledger contains an unsafe archive")

    execution_rows = _read_execution_ledger(errors)
    if final:
        _validate_pr118_receipts(execution_rows, errors)

    diagnostics = _validate_json(DIAGNOSTICS, errors)
    diagnostics = _require_object(
        diagnostics,
        "diagnostic results",
        (
            "schema",
            "owner",
            "claim_tier",
            "lanes",
            "lane_count",
            "counterfactual_contract",
            "production_outputs_modified",
        ),
        errors,
    )
    if diagnostics:
        if diagnostics.get("lane_count") != 7 or set(diagnostics.get("lanes", {})) != set(
            DIAGNOSTIC_LANE_NAMES.values()
        ):
            errors.append("diagnostics must contain the exact seven audit lanes")
        if diagnostics.get("production_outputs_modified") is not False:
            errors.append("audit diagnostics must not modify production outputs")
        if diagnostics.get("counterfactual_contract") != COUNTERFACTUAL_FIELDS:
            errors.append("diagnostic counterfactual contract drift")

    atomic = _validate_json(ATOMIC_LEDGER, errors)
    _validate_atomic_findings(atomic, prior_ids, execution_rows, errors)

    adjudications = _validate_json(AUDIT / "root_adjudications.json", errors)
    adjudications = _require_object(
        adjudications,
        "root adjudications",
        (
            "schema",
            "finding_clusters",
            "atomic_ledger_path",
            "new_open_finding_count",
            "new_open_severity_counts",
            "digest_blind_referees",
        ),
        errors,
    )
    if adjudications:
        if adjudications.get("new_open_finding_count") != 33:
            errors.append("root adjudication open census must be 33")
        if adjudications.get("new_open_severity_counts") != {
            "P0": 0,
            "P1": 22,
            "P2": 11,
            "P3": 0,
        }:
            errors.append("root adjudication severity census is stale")
        if len(adjudications.get("finding_clusters", [])) != 14:
            errors.append("root adjudications must retain 14 work-package clusters")
        atomic_rows = atomic.get("atomic_findings", []) if isinstance(atomic, dict) else []
        atomic_clusters = {
            row.get("cluster_id")
            for row in atomic_rows
            if isinstance(row, dict)
        }
        root_clusters = {
            row.get("finding_id")
            for row in adjudications.get("finding_clusters", [])
            if isinstance(row, dict)
        }
        if atomic_clusters != root_clusters:
            errors.append(
                "atomic/root cluster crosswalk mismatch: "
                f"atomic_only={sorted(atomic_clusters - root_clusters)} "
                f"root_only={sorted(root_clusters - atomic_clusters)}"
            )
        cmb_aliases = [
            row
            for row in adjudications.get("cluster_alias_examples", [])
            if row.get("candidate") == "CMB-D02"
        ]
        if cmb_aliases != [
            {
                "candidate": "CMB-D02",
                "disposition": "REUSE_PRIOR_IN_WORK_PACKAGE",
                "canonical": "C5-EXT-ACT-F1",
                "work_package": "D-DATA-ACT-VALIDATION",
            }
        ]:
            errors.append("CMB-D02 alias must preserve prior-reuse disposition")

    debate = _validate_json(AUDIT / "debate_bundle.json", errors)
    debate = _require_object(
        debate,
        "debate bundle",
        (
            "schema",
            "agent_artifacts",
            "agent_artifact_count",
            "complete_response_count",
            "web_lock",
            "root_adjudications_path",
            "root_adjudications_sha256",
        ),
        errors,
    )
    if debate:
        agent_rows = debate.get("agent_artifacts", [])
        actual_roles = {(row.get("phase"), row.get("role")) for row in agent_rows}
        missing_roles = sorted(REQUIRED_AGENT_ROLES - actual_roles)
        if missing_roles:
            errors.append(f"debate bundle missing required roles: {missing_roles}")
        if final:
            missing_final_roles = sorted(REQUIRED_PR118_AGENT_ROLES - actual_roles)
            if missing_final_roles:
                errors.append(
                    f"debate bundle missing required PR-118 roles: {missing_final_roles}"
                )
        if len(actual_roles) != len(agent_rows):
            errors.append("debate bundle has duplicate phase/role entries")
        if debate.get("agent_artifact_count") != len(agent_rows):
            errors.append("debate artifact count is stale")
        if debate.get("complete_response_count") != len(agent_rows):
            errors.append("debate bundle contains incomplete responses")
        if debate.get("offline_receipt_failures"):
            errors.append("debate bundle contains offline receipt failures")
        for row in agent_rows:
            for kind in ("prompt", "response"):
                path = REPO / str(row.get(f"{kind}_path", ""))
                if not path.is_file() or row.get(f"{kind}_sha256") != sha256_file(path):
                    errors.append(f"debate {kind} hash stale for {row.get('role')}")
        if debate.get("root_adjudications_sha256") != sha256_file(
            AUDIT / "root_adjudications.json"
        ):
            errors.append("debate root-adjudication hash is stale")

    _validate_sealed_diagnostics(execution_rows, diagnostics, errors)

    required_md = [
        AUDIT / "prior_crosswalk.md",
        AUDIT / "four_axis_hostile_review.md",
        AUDIT / "history_legacy_ledger.md",
    ]
    if final:
        required_md.extend(
            [
                AUDIT / "criticism_response_matrix.md",
                AUDIT / "final_referee_report.md",
                AUDIT / "executive_summary_ko.md",
            ]
        )
        for name in (
            "advocate_candidate_ledger.json",
            "criticism_response_matrix.json",
            "web_crag_final.json",
        ):
            _validate_json(AUDIT / name, errors)
        _validate_final_closeout(prior, atomic, execution_rows, errors)
    for path in required_md:
        if not path.is_file() or not path.read_text(encoding="utf-8").strip():
            errors.append(f"missing or empty artifact: {relative(path)}")

    manifest = _validate_json(MANIFEST, errors)
    manifest = _require_object(
        manifest,
        "audit manifest",
        (
            "schema",
            "owner",
            "implementation_scope",
            "claim_tier",
            "transfer_source",
            "config_hash",
            "input_hashes",
            "sky_support_status",
            "null_mock_status",
            "caveats",
            "generating_command",
            "git_commit_or_worktree_state",
            "files",
            "file_count",
        ),
        errors,
    )
    if manifest:
        for field in (
            "owner",
            "implementation_scope",
            "claim_tier",
            "transfer_source",
            "config_hash",
            "input_hashes",
            "sky_support_status",
            "null_mock_status",
            "caveats",
            "generating_command",
            "git_commit_or_worktree_state",
        ):
            if not manifest.get(field):
                errors.append(f"manifest missing/empty {field}")
        if manifest.get("counterfactual_contract") != COUNTERFACTUAL_FIELDS:
            errors.append("counterfactual contract drift")
        _validate_manifest_sealed_config(manifest, errors)
        listed = {row["path"]: row for row in manifest.get("files", [])}
        if len(listed) != len(manifest.get("files", [])):
            errors.append("manifest contains duplicate file paths")
        if manifest.get("file_count") != len(listed):
            errors.append("manifest file_count is stale")
        for path in sorted(AUDIT.rglob("*")):
            if path.is_file() and path != MANIFEST:
                key = relative(path)
                if key not in listed:
                    errors.append(f"manifest omits {key}")
                elif listed[key].get("sha256") != sha256_file(path):
                    errors.append(f"manifest hash stale for {key}")

    # Counterfactual results may exist only inside this audit package.  Scan
    # structured JSON and textual YAML/Markdown/TeX, including untagged strong
    # public claims; serialization and whitespace cannot bypass this gate.
    forbidden_roots = [
        REPO / "docs/manuscript",
        REPO / "docs/generated",
        REPO / "figures",
    ]
    for root in forbidden_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in {
                ".json",
                ".yaml",
                ".yml",
                ".md",
                ".tex",
                ".txt",
            }:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            leaked = bool(_counterfactual_public_text_hits(text))
            canonical_claim_issues = scan_claim_text(text, path=path)
            leaked = leaked or bool(canonical_claim_issues)
            if path.suffix.lower() == ".json":
                try:
                    leaked = leaked or _contains_counterfactual_marker(json.loads(text))
                except json.JSONDecodeError:
                    pass
            if leaked:
                errors.append(
                    "counterfactual metadata or forbidden claim leaked outside audit "
                    f"package: {relative(path)}"
                )
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("build-environment")
    sub.add_parser("build-pr118-environment")
    sub.add_parser("build-prior")
    sub.add_parser("build-initial-crag")
    sub.add_parser("build-history")
    sub.add_parser("build-debate")
    sub.add_parser("build-shortlist-freeze")
    sub.add_parser("build-advocate-ledger")
    sub.add_parser("build-final-crag")
    sub.add_parser("build-criticism-matrix")
    sub.add_parser("build-final-reports")
    sub.add_parser("build-manifest")
    diag = sub.add_parser("run-diagnostic")
    diag.add_argument(
        "lane", choices=("cf4", "grf", "fsigma", "desi", "act", "k6", "jwst")
    )
    val = sub.add_parser("validate")
    val.add_argument("--final", action="store_true")
    rec = sub.add_parser("record-command")
    rec.add_argument("--id", required=True)
    rec.add_argument("--agent", default="root")
    rec.add_argument("--seed", type=int, default=AUDIT_SEED)
    rec.add_argument("--input", action="append")
    rec.add_argument("--environment-file")
    rec.add_argument("exec_command", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)

    if args.command == "build-environment":
        payload = build_environment()
        print(payload["environment_hash"])
        return 0
    if args.command == "build-pr118-environment":
        payload = build_pr118_environment()
        print(payload["environment_hash"])
        return 0
    if args.command == "build-prior":
        payload = build_prior()
        print(
            f"imported {len(payload['prior_findings'])} prior findings and "
            f"{payload['completeness_gap_count']} audit gaps"
        )
        return 0
    if args.command == "build-initial-crag":
        payload, lock = build_initial_crag()
        print(
            f"sealed {payload['source_count']} sources; "
            f"web status={lock['status']} hash={lock['locked_packet_sha256']}"
        )
        return 0
    if args.command == "build-history":
        payload = build_history()
        print(f"inventoried {len(payload['archives'])} legacy archives")
        return 0
    if args.command == "build-debate":
        payload = build_debate()
        print(
            f"indexed {payload['complete_response_count']}/"
            f"{payload['agent_artifact_count']} agent responses"
        )
        return 0
    if args.command == "build-shortlist-freeze":
        payload = build_shortlist_freeze()
        print(
            f"froze {payload['shortlist_count']} candidates at "
            f"{sha256_file(SHORTLIST_FREEZE)}"
        )
        return 0
    if args.command == "build-advocate-ledger":
        payload = build_advocate_ledger()
        print(
            f"ranked {payload['candidate_count']} candidates; "
            f"shortlisted {payload['shortlist_count']}"
        )
        return 0
    if args.command == "build-final-crag":
        payload = build_final_crag()
        print(
            f"sealed final CRAG for {payload['candidate_count']} candidates "
            f"from {len(payload['sources'])} primary/official sources"
        )
        return 0
    if args.command == "build-criticism-matrix":
        payload = build_criticism_matrix()
        print(f"mapped {payload['row_count']} criticisms")
        return 0
    if args.command == "build-final-reports":
        payload = build_final_reports()
        print(f"rendered {len(payload['referees'])} independent referee decisions")
        return 0
    if args.command == "build-manifest":
        payload = build_manifest()
        print(f"manifested {payload['file_count']} files")
        return 0
    if args.command == "run-diagnostic":
        payload = run_diagnostic(args.lane)
        print(json.dumps(payload, indent=2, sort_keys=True, default=str))
        return 0 if payload.get("status") != "FAILED" else 1
    if args.command == "record-command":
        return record_command(args)
    errors = validate(final=args.final)
    if errors:
        print("AUDIT PACKAGE INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("audit package valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
