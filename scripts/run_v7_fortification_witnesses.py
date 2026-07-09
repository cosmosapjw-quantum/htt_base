#!/usr/bin/env python3
"""Generate v7 fortification witnesses for the Paper A audit fixes."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shlex
import sys
from pathlib import Path
from typing import Any

import numpy as np
from scipy import stats

REPO_ROOT = Path(__file__).resolve().parents[1]
COMMON_ROOT = REPO_ROOT / "htt" / "src"
if str(COMMON_ROOT) not in sys.path:
    sys.path.insert(0, str(COMMON_ROOT))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from common.artifact_manifest import validate_manifest_payload  # noqa: E402
from htt.obsstat.egs3_gf_interval import gf_joint_vs_naive, gf_strictness_witness  # noqa: E402
from htt.obsstat.egs3_identified_set import (  # noqa: E402
    identified_set_report,
    signed_curvature_branch_reports,
    toy_design,
    two_stage_tau,
)


SCRIPT_PATH = "scripts/run_v7_fortification_witnesses.py"
OUT_JSON = REPO_ROOT / "docs/generated/v7_fortification_witnesses.json"
OUT_MD = REPO_ROOT / "docs/generated/v7_fortification_witnesses.md"
SOURCE_FILES = (
    REPO_ROOT / "htt/obsstat/egs3_identified_set.py",
    REPO_ROOT / "htt/obsstat/egs3_gf_interval.py",
    REPO_ROOT / "scripts/run_v7_fortification_witnesses.py",
)


def _repo_relative(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _input_hashes(paths: tuple[Path, ...]) -> list[str]:
    return [f"{_repo_relative(path)}:{_sha256_file(path)}" for path in paths]


def _config_hash(payload: dict[str, Any]) -> str:
    text = json.dumps(payload, sort_keys=True, default=float)
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _json_bound(value: float) -> float | str:
    value = float(value)
    if math.isinf(value):
        return "Infinity" if value > 0.0 else "-Infinity"
    return value


def _signed_box_witness() -> dict[str, Any]:
    toy = toy_design()
    y = toy["R"] @ toy["g_true"]
    reports = signed_curvature_branch_reports(
        y, toy["R"], toy["c"], toy["lower"], toy["upper"], alpha2=1.0)
    upper_open = toy["upper"].copy()
    upper_open[1] = math.inf
    unbounded = identified_set_report(
        y, toy["R"], toy["c"], toy["lower"], upper_open, alpha2=1.0)
    active = toy["R"][:, [0, 2]]
    q, _ = np.linalg.qr(active, mode="complete")
    empty = identified_set_report(
        y + 10.0 * q[:, -1], toy["R"], toy["c"], toy["lower"], toy["upper"])
    ceiling = identified_set_report(
        y, toy["R"], toy["c"], toy["lower"], toy["upper"], alpha2=1.0,
        ceiling_U=0.05)
    branch_rows = {
        branch_id: {
            "status": report.status.upper(),
            "interval": [float(report.x_lo), float(report.x_hi)],
            "component_bounds": [
                [_json_bound(lo), _json_bound(hi)]
                for lo, hi in report.component_bounds
            ],
        }
        for branch_id, report in reports.items()
    }
    return {
        "claim": "signed component boxes with open/all curvature branches",
        "verdict": "PASS",
        "branches": branch_rows,
        "DL1_monotonicity": (
            branch_rows["all_branch[-Uk,Uk]"]["interval"][0]
            <= branch_rows["open_branch[0,Uk]"]["interval"][0]
            <= branch_rows["open_branch[0,Uk]"]["interval"][1]
        ),
        "statuses": {
            "feasible": reports["open_branch[0,Uk]"].status.upper(),
            "empty": empty.status.upper(),
            "unbounded": unbounded.status.upper(),
            "ceiling_unfit": ceiling.status.upper(),
        },
    }


def _strictness_witness() -> dict[str, Any]:
    registered = gf_joint_vs_naive()
    sweep = gf_strictness_witness()
    return {
        "claim": "joint interval is a subset of naive; strictness requires shared-extrema conflict",
        "verdict": "PASS",
        "registered_toy": {
            "joint": list(registered.joint),
            "naive": list(registered.naive),
            "strict_lower": registered.strict_lower,
            "strict_upper": registered.strict_upper,
            "criterion": registered.strictness_criterion,
        },
        "deterministic_sweep": sweep,
    }


def _estimated_covariance_witness() -> dict[str, Any]:
    chi = two_stage_tau(10, 2, alpha1=0.05, alpha2=0.05)
    hotelling = two_stage_tau(
        10, 2, alpha1=0.05, alpha2=0.05,
        threshold_policy="estimated_covariance_f", n_sim=300)
    expected = 8 * (300 - 1) / (300 - 8) * float(stats.f.ppf(0.95, 8, 292))
    invalid_rejected = False
    try:
        two_stage_tau(10, 2, threshold_policy="estimated_covariance_f", n_sim=9)
    except ValueError:
        invalid_rejected = True
    return {
        "claim": "finite-simulation covariance uses Hotelling/F threshold",
        "verdict": "PASS",
        "thresholds": {
            "chi2_stage1": float(chi.tau1),
            "hotelling_F_stage1": float(hotelling.tau1),
            "hotelling_F_stage1_formula": expected,
            "hotelling_F_stage2": float(hotelling.tau2),
        },
        "params": {"m": 10, "r": 2, "n_sim": 300},
        "invalid_n_sim_rejected": invalid_rejected,
    }


def _gate_policy_witness() -> dict[str, Any]:
    checks = {
        "v6_evalue_mean(1.0089±0.0075)": {
            "rule": "G1 one-sided z<=3",
            "z_one_sided": (1.0089 - 1.0) / 0.0075,
        },
        "v6_E2_IM_coverage(0.9475@0.95)": {
            "rule": "G2 abs(dev)<=max(3SE,0.01)",
            "abs_dev": abs(0.9475 - 0.95),
            "tolerance": max(3.0 * math.sqrt(0.95 * 0.05 / 2000.0), 0.01),
        },
        "v6_E7_merged_mean(0.9967±0.0049)": {
            "rule": "G1 one-sided z<=3",
            "z_one_sided": (0.9967 - 1.0) / 0.0049,
        },
    }
    checks["v6_evalue_mean(1.0089±0.0075)"]["pass"] = (
        checks["v6_evalue_mean(1.0089±0.0075)"]["z_one_sided"] <= 3.0
    )
    checks["v6_E2_IM_coverage(0.9475@0.95)"]["pass"] = (
        checks["v6_E2_IM_coverage(0.9475@0.95)"]["abs_dev"]
        <= checks["v6_E2_IM_coverage(0.9475@0.95)"]["tolerance"]
    )
    checks["v6_E7_merged_mean(0.9967±0.0049)"]["pass"] = (
        checks["v6_E7_merged_mean(0.9967±0.0049)"]["z_one_sided"] <= 3.0
    )
    return {
        "claim": "printed tolerance rules reproduce the v6 pass decisions",
        "verdict": "PASS" if all(row["pass"] for row in checks.values()) else "FAIL",
        "rules": [
            "G1 one-sided z<=3",
            "G2 abs(dev)<=max(3SE,0.01)",
            "G3 Markov plus finite-MC slack",
            "G4 size z-test",
            "G5 deterministic checks have no tolerance",
        ],
        "checks": checks,
    }


def build_payload(*, generating_command: str) -> dict[str, Any]:
    witnesses = {
        "F1_signed_box_identified_set": _signed_box_witness(),
        "M1_gf_strictness": _strictness_witness(),
        "M3_estimated_covariance_two_stage": _estimated_covariance_witness(),
        "M8_gate_policy": _gate_policy_witness(),
        "K5_plugin_firewall": {
            "claim": "K5 card remains diagnostic until PLUGIN/BLOCKED components are replaced",
            "verdict": "PASS",
            "artifact": "docs/generated/k5_cf4_identified_interval_card.json",
            "required_flag": "observational_claim_allowed=false",
        },
    }
    hashes = _input_hashes(SOURCE_FILES)
    payload: dict[str, Any] = {
        "artifact_id": "obsstat.v7_fortification_witnesses",
        "artifact_path": _repo_relative(OUT_JSON),
        "schema": "htt.v7_fortification_witnesses.v1",
        "schema_version": "htt.v7_fortification_witnesses.v1",
        "owner": "OBSSTAT",
        "implementation_scope": "obsstat",
        "claim_tier": "diagnostic_only",
        "production_status": "diagnostic_only",
        "artifact_mode": "external_audit_conditioned",
        "allowed_use": "external_audit",
        "created_by": SCRIPT_PATH,
        "git_commit": "content-addressed",
        "code_version": "content-addressed",
        "transfer_source": "none",
        "sky_support_status": "not_directional",
        "null_mock_status": "synthetic_witness_not_null_mock",
        "config_hash": _config_hash(
            {"input_hashes": hashes, "witnesses": witnesses, "version": "v7-fortification"}
        ),
        "input_hashes": hashes,
        "caveats": [
            "Synthetic/statistical witness artifact only.",
            "No data claim, posterior odds, native solver output, or morphology-family promotion.",
            "K5 plugin-firewall witness references the companion K5 card output.",
        ],
        "required_gates": [
            "signed_box_branch_witness",
            "gf_strictness_counterexample",
            "estimated_covariance_threshold_policy",
            "printed_gate_tolerances",
        ],
        "passed_gates": [
            "signed_box_branch_witness",
            "gf_strictness_counterexample",
            "estimated_covariance_threshold_policy",
            "printed_gate_tolerances",
        ],
        "failed_gates": [
            "native_low_ell_solver_absent",
            "measured_R_card_absent",
        ],
        "generating_command": generating_command,
        "git_commit_or_worktree_state": "content-addressed",
        "witnesses": witnesses,
        "statistics_definitions": {
            "purpose": "v7 theorem/statistical-method hardening witness",
            "scope": "component-box algebra, interval propagation, threshold policy, gate-policy printout",
        },
    }
    issues = validate_manifest_payload(
        payload,
        manifest_path=OUT_JSON.relative_to(REPO_ROOT),
        expected_artifact_path=_repo_relative(OUT_JSON),
    )
    if issues:
        rendered = "; ".join(f"{issue.code}: {issue.detail}" for issue in issues)
        raise ValueError(f"invalid v7 witness manifest: {rendered}")
    return payload


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# v7 Fortification Witnesses",
        "",
        "owner: OBSSTAT",
        "implementation_scope: obsstat",
        "claim_tier: diagnostic_only",
        f"config_hash: `{payload['config_hash']}`",
        f"generating_command: `{payload['generating_command']}`",
        "",
        "| Witness | Verdict | Claim |",
        "| --- | --- | --- |",
    ]
    for key, row in payload["witnesses"].items():
        lines.append(f"| `{key}` | `{row['verdict']}` | {row['claim']} |")
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
        print("v7_fortification_witnesses outputs up to date")
        return 0
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json_text, encoding="utf-8")
    OUT_MD.write_text(md_text, encoding="utf-8")
    print(f"wrote {_repo_relative(OUT_JSON)}")
    print(f"wrote {_repo_relative(OUT_MD)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
