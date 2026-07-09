#!/usr/bin/env python3
"""Build the K5/CF4 identified-interval diagnostic card.

This closes the v7 audit's end-to-end wiring check using repo-local generated
artifacts only. It is deliberately not an observational x_C result: Sigma^2,
W^2, and Omega_k pieces remain PLUGIN/BLOCKED until registered artifacts replace
the placeholders.
"""
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

REPO_ROOT = Path(__file__).resolve().parents[1]
COMMON_ROOT = REPO_ROOT / "htt" / "src"
if str(COMMON_ROOT) not in sys.path:
    sys.path.insert(0, str(COMMON_ROOT))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from common.artifact_manifest import validate_manifest_payload  # noqa: E402
from htt.obsstat.egs3_identified_set import (  # noqa: E402
    im_interval,
    signed_curvature_branch_reports,
)
from htt.obsstat.egs3_mes_provenance import eps_registry_provenance  # noqa: E402

# Registered W^2 ceiling from the MES budget (ssot Planck Commander epsilons):
# W2_max = (3/2) B_omega^2. Replaces the earlier toy plugin (which was ~46% low).
W2_REGISTERED_UPPER = float(
    eps_registry_provenance()["registered_ceilings_from_ssot"]["W2_max"])


OUT_JSON = REPO_ROOT / "docs/generated/k5_cf4_identified_interval_card.json"
OUT_MD = REPO_ROOT / "docs/generated/k5_cf4_identified_interval_card.md"
K5_COVERAGE = REPO_ROOT / "docs/generated/k5_cf4_release_coverage.json"
K1_MAXSCAN = REPO_ROOT / "docs/generated/k1_global_maxscan.json"
PARENT_SEAL = REPO_ROOT / "docs/generated/parent_identity_seal.json"
OBS_DEFAULTS = REPO_ROOT / "htt/workspace/data/obs_defaults.json"
SCRIPT_PATH = "scripts/k5_cf4_identified_interval_card.py"
LIGHT_SPEED_KMS = 299792.458

# Explicit blocked placeholders. They exist only to exercise the branch/status
# algebra until real registered artifacts bind these components.
SIGMA2_PLUGIN_VALUE = 1.0e-5
SIGMA2_PLUGIN_ERROR_FRACTION = 0.63
W2_PLUGIN_UPPER = 8.959622448979593e-7
OMEGA_K_PLUGIN_UPPER = 1.0e-6


def _repo_relative(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _input_hashes(paths: tuple[Path, ...]) -> list[str]:
    rows = []
    for path in paths:
        rows.append(f"{_repo_relative(path)}:{_sha256_file(path)}")
    return rows


def _config_hash(payload: dict[str, Any]) -> str:
    text = json.dumps(payload, sort_keys=True, default=float)
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _json_bound(value: float) -> float | str:
    value = float(value)
    if math.isinf(value):
        return "Infinity" if value > 0.0 else "-Infinity"
    return value


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _omega_tilt_from_bulk(*, bulk_amp_kms: float, bulk_err_kms: float,
                          omega_m: float, w: float = 0.0) -> dict[str, float]:
    beta = float(bulk_amp_kms) / LIGHT_SPEED_KMS
    value = (1.0 + float(w)) * float(omega_m) * math.sinh(beta) ** 2
    deriv = (1.0 + float(w)) * float(omega_m) * 2.0 * math.sinh(beta) * math.cosh(beta)
    err = abs(deriv) * float(bulk_err_kms) / LIGHT_SPEED_KMS
    return {"beta": beta, "omega_tilt": value, "omega_tilt_error": err}


def _branch_payloads(*, omega_tilt: float, omega_tilt_error: float,
                     policy_id: str) -> dict[str, Any]:
    sigma2_error = SIGMA2_PLUGIN_ERROR_FRACTION * SIGMA2_PLUGIN_VALUE
    response = np.zeros((4, 4), dtype=float)
    response[0, 0] = 1.0 / sigma2_error
    response[1, 2] = 1.0 / omega_tilt_error
    g_hat = np.array([SIGMA2_PLUGIN_VALUE, 0.0, omega_tilt, 0.0], dtype=float)
    y = response @ g_hat
    c = np.array([1.0, -1.0, 1.0, 1.0], dtype=float)
    lower = np.zeros(4, dtype=float)
    upper = np.array([np.inf, W2_REGISTERED_UPPER, np.inf, OMEGA_K_PLUGIN_UPPER], dtype=float)
    input_modes = (
        ("Sigma2", "PLUGIN/BLOCKED"),
        ("W2_upper", "REGISTERED_MES_CEILING"),
        ("Omega_tilt", "REAL_CF4_PLUS_DECLARED_OMEGA_M"),
        ("Omega_k_upper", "PLUGIN/BLOCKED"),
    )
    reports = signed_curvature_branch_reports(
        y,
        response,
        c,
        lower,
        upper,
        alpha1=0.05,
        alpha2=0.05,
        input_modes=input_modes,
        observational_claim_allowed=False,
    )
    rows: dict[str, Any] = {}
    endpoint_se = math.sqrt(sigma2_error ** 2 + omega_tilt_error ** 2)
    for branch_id, report in reports.items():
        im_lo, im_hi, cn = im_interval(report.x_lo, report.x_hi, endpoint_se, endpoint_se)
        rows[branch_id] = {
            "status": report.status.upper(),
            "interval": [float(report.x_lo), float(report.x_hi)],
            "reachable_extremes": [float(report.reachable_lo), float(report.reachable_hi)],
            "null_extremes": [float(report.null_lo), float(report.null_hi)],
            "spec_stat": float(report.spec_stat),
            "tau1": float(report.tau.tau1),
            "tau2": float(report.tau.tau2),
            "threshold_policy": report.threshold_policy,
            "df_residual": report.df_residual,
            "df_reachable": report.df_reachable,
            "component_bounds": [
                [_json_bound(lo), _json_bound(hi)]
                for lo, hi in report.component_bounds
            ],
            "im_95_ci": [float(im_lo), float(im_hi)],
            "im_c_n": float(cn),
            "policy_id": policy_id,
        }
    return rows


def build_payload(*, generating_command: str) -> dict[str, Any]:
    for path in (K5_COVERAGE, K1_MAXSCAN, PARENT_SEAL, OBS_DEFAULTS):
        if not path.is_file():
            raise FileNotFoundError(f"required artifact missing: {_repo_relative(path)}")
    k5 = _read_json(K5_COVERAGE)
    k1 = _read_json(K1_MAXSCAN)
    parent = _read_json(PARENT_SEAL)
    obs = _read_json(OBS_DEFAULTS)

    bulk = k5["measured_bulk"]
    coverage = k5["coverage"]
    omega_m = float(obs["Omega_m"])
    policies = {
        "measurement_only": float(bulk["amplitude_error_kms"]),
        "cosmic_variance_inclusive": float(coverage["total_amplitude_error_kms"]),
    }
    policy_rows: dict[str, Any] = {}
    for policy_id, bulk_err in policies.items():
        tilt = _omega_tilt_from_bulk(
            bulk_amp_kms=float(bulk["amplitude_kms"]),
            bulk_err_kms=bulk_err,
            omega_m=omega_m,
        )
        policy_rows[policy_id] = {
            "bulk_error_kms": bulk_err,
            **tilt,
            "branches": _branch_payloads(
                omega_tilt=tilt["omega_tilt"],
                omega_tilt_error=max(tilt["omega_tilt_error"], 1e-15),
                policy_id=policy_id,
            ),
        }

    inputs = (K5_COVERAGE, K1_MAXSCAN, PARENT_SEAL, OBS_DEFAULTS)
    hashes = _input_hashes(inputs)
    component_modes = {
        "CF4_bulk_amplitude": "REAL",
        "Omega_m": "DECLARED_OBS_DEFAULT",
        "Omega_tilt_formula": "DERIVED_FROM_PARENT_IDENTITY_SEAL",
        "Sigma2_hat": "PLUGIN/BLOCKED",
        "Sigma2_error": "PLUGIN/BLOCKED",
        "W2_upper": "REGISTERED_MES_CEILING",
        "Omega_k_upper": "PLUGIN/BLOCKED",
        "K1_maxscan": "REAL_DIAGNOSTIC_INPUT_NOT_USED_AS_SIGMA2",
        "MES_coefficients": "REGISTERED_EXTERNAL_NOT_REDERIVED",
    }
    blocked = [key for key, mode in component_modes.items() if "PLUGIN/BLOCKED" in mode]
    payload: dict[str, Any] = {
        "artifact_id": "obsstat.k5_cf4_identified_interval_card",
        "artifact_path": _repo_relative(OUT_JSON),
        "schema": "htt.k5.cf4_identified_interval_card.v1",
        "schema_version": "htt.k5.cf4_identified_interval_card.v1",
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
        "null_mock_status": "not_statistical",
        "input_hashes": hashes,
        "config_hash": _config_hash(
            {
                "inputs": hashes,
                "policies": policies,
                "plugin_placeholders": {
                    "Sigma2": SIGMA2_PLUGIN_VALUE,
                    "Sigma2_error_fraction": SIGMA2_PLUGIN_ERROR_FRACTION,
                    "Omega_k_upper": OMEGA_K_PLUGIN_UPPER,
                },
                "registered_ceilings": {
                    "W2_upper_from_mes": W2_REGISTERED_UPPER,
                },
                "version": "v7-k5-identified-interval-card",
            }
        ),
        "caveats": [
            "Diagnostic pipeline-closure card only.",
            "W2 ceiling is the registered MES value (3/2)B_omega^2 from the ssot epsilons.",
            "Sigma2 and Omega_k placeholders still block observational promotion.",
            "No posterior odds, native low-ell solver output, or morphology-family promotion.",
        ],
        "required_gates": [
            "repo_local_cf4_bulk_artifact_present",
            "parent_identity_formula_present",
            "plugin_firewall_for_unbound_components",
        ],
        "passed_gates": [
            "repo_local_cf4_bulk_artifact_present",
            "parent_identity_formula_present",
            "plugin_firewall_for_unbound_components",
            "registered_w2_ceiling_from_mes_provenance",
        ],
        "failed_gates": [
            "registered_sigma2_artifact_absent",
            "registered_omega_k_upper_artifact_absent",
        ],
        "promotion_blockers": blocked,
        "generating_command": generating_command,
        "git_commit_or_worktree_state": "content-addressed",
        "family_identification": False,
        "native_solver_result": False,
        "observational_claim_allowed": False,
        "blocked_components": blocked,
        "component_input_modes": component_modes,
        "source_artifacts": [_repo_relative(path) for path in inputs],
        "bulk_flow_summary": {
            "amplitude_kms": float(bulk["amplitude_kms"]),
            "measurement_error_kms": float(bulk["amplitude_error_kms"]),
            "total_error_kms": float(coverage["total_amplitude_error_kms"]),
            "n_groups": int(bulk["n_groups"]),
            "sigma_cv_prior_kms_per_component": float(coverage["sigma_cv_prior_kms_per_component"]),
        },
        "k1_context": {
            "smica_global_p": float(k1["smica"]["global_p"]),
            "commander_global_p": float(k1["commander"]["global_p"]),
            "use_in_card": "context_only_not_sigma2_binding",
        },
        "parent_identity": {
            "omega_tilt_closed_form": parent["parent_identity"]["omega_tilt_closed_form"],
            "mes_epsilon_rederived_here": bool(
                parent["mes_epsilon_provenance"]["rederived_here"]),
        },
        "policies": policy_rows,
        "statistics_definitions": {
            "x_comparator": "c=(1,-1,1,1) applied to branch-bounded components",
            "omega_tilt": "(1+w) Omega_m sinh(beta)^2 with w=0 and beta=|B|/c",
            "error_policies": list(policies),
            "plugin_firewall": "observational_claim_allowed is false while any component is PLUGIN/BLOCKED",
        },
    }
    issues = validate_manifest_payload(
        payload,
        manifest_path=OUT_JSON.relative_to(REPO_ROOT),
        expected_artifact_path=_repo_relative(OUT_JSON),
    )
    if issues:
        rendered = "; ".join(f"{issue.code}: {issue.detail}" for issue in issues)
        raise ValueError(f"invalid K5 card manifest: {rendered}")
    return payload


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# K5 CF4 Identified-Interval Diagnostic Card",
        "",
        "owner: OBSSTAT",
        "implementation_scope: obsstat",
        "claim_tier: diagnostic_only",
        "artifact_mode: external_audit_conditioned",
        f"config_hash: `{payload['config_hash']}`",
        f"generating_command: `{payload['generating_command']}`",
        "observational_claim_allowed: false",
        "",
        "## Component Modes",
        "",
        "| Component | Input mode |",
        "| --- | --- |",
    ]
    for key, mode in payload["component_input_modes"].items():
        lines.append(f"| {key} | `{mode}` |")
    lines.extend([
        "",
        "## Branch Intervals",
        "",
        "| Policy | Branch | Status | Interval | IM 95% CI |",
        "| --- | --- | --- | --- | --- |",
    ])
    for policy_id, policy in payload["policies"].items():
        for branch_id, branch in policy["branches"].items():
            interval = branch["interval"]
            im_ci = branch["im_95_ci"]
            lines.append(
                f"| `{policy_id}` | `{branch_id}` | `{branch['status']}` | "
                f"[{interval[0]:.6e}, {interval[1]:.6e}] | "
                f"[{im_ci[0]:.6e}, {im_ci[1]:.6e}] |"
            )
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
        print("k5_cf4_identified_interval_card outputs up to date")
        return 0
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json_text, encoding="utf-8")
    OUT_MD.write_text(md_text, encoding="utf-8")
    print(f"wrote {_repo_relative(OUT_JSON)}")
    print(f"wrote {_repo_relative(OUT_MD)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
