#!/usr/bin/env python3
"""K5/CF4 identified-interval card, v9 (NEW artifact; REV-R173).

Answers R2's V3 (dual-branch W^2 ceiling) and R1 3.5 (attribution split) from
the 2026-07-10 reviews: the card now carries the identified interval under
ALL THREE attribution-conditional W^2 ceilings of the MES branch registry
(egs3_mes_branch_registry), each crossed with the two signed-curvature
branches of the DL1 machinery:

  W2_registered        1.3087e-6  (MES_NG coefficients; UNVERIFIED provenance;
                                   the frozen bit-identity anchor — unchanged)
  W2_hybrid_literature 2.5369e-5  (MES_G geodesic coefficients x the FULL
                                   observer dipole; comparison-only hybrid)
  W2_sag_consistent    3.379e-13  (MES_G under SAG's own eps1 = 0)

Because c_W = -1 the W^2 ceiling fixes the LOWER endpoint; the spread across
branches quantifies exactly how much the interval is keyed to the eps1
attribution choice (the dominance disclosure of the branch registry). No
branch is promoted; the registered branch remains the frozen anchor.

The frozen v7 card and the v8 extension card are carried by reference
(path + SHA256) and are NOT modified; their contract tests pin their own
branch-key sets, which is why this is a successor artifact with schema
``htt.k5.cf4_identified_interval_card.v2``.

``observational_claim_allowed`` stays False; the plugin firewall is intact.
``--check`` regenerates in memory and diffs against disk.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
for p in (REPO_ROOT / "htt/src", REPO_ROOT / "htt/htt", REPO_ROOT / "htt",
          REPO_ROOT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from common.artifact_manifest import validate_manifest_payload  # noqa: E402
from htt.obsstat.egs3_identified_set import (  # noqa: E402
    im_interval,
    signed_curvature_branch_reports,
)
from htt.obsstat.egs3_mes_branch_registry import (  # noqa: E402
    w2_ceiling_branches,
    eps1_attribution_triple,
)

OUT_JSON = REPO_ROOT / "docs/generated/k5_cf4_identified_interval_card_v9.json"
OUT_MD = REPO_ROOT / "docs/generated/k5_cf4_identified_interval_card_v9.md"
FROZEN_V7_CARD = REPO_ROOT / "docs/generated/k5_cf4_identified_interval_card.json"
FROZEN_V8_CARD = REPO_ROOT / "docs/generated/k5_cf4_identified_interval_card_v8.json"
K5_COVERAGE = REPO_ROOT / "docs/generated/k5_cf4_release_coverage.json"
OBS_DEFAULTS = REPO_ROOT / "htt/workspace/data/obs_defaults.json"
SCRIPT_PATH = "scripts/k5_cf4_identified_interval_card_v9.py"
LIGHT_SPEED_KMS = 299792.458

# plugin placeholders identical to the frozen v7 card (unchanged semantics)
SIGMA2_PLUGIN_VALUE = 1.0e-5
SIGMA2_PLUGIN_ERROR_FRACTION = 0.63
OMEGA_K_PLUGIN_UPPER = 1.0e-6


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _omega_tilt_from_bulk(*, bulk_amp_kms: float, bulk_err_kms: float,
                          omega_m: float, w: float = 0.0) -> dict[str, float]:
    beta = float(bulk_amp_kms) / LIGHT_SPEED_KMS
    value = (1.0 + float(w)) * float(omega_m) * math.sinh(beta) ** 2
    deriv = (1.0 + float(w)) * float(omega_m) * 2.0 * math.sinh(beta) * math.cosh(beta)
    err = abs(deriv) * float(bulk_err_kms) / LIGHT_SPEED_KMS
    return {"beta": beta, "omega_tilt": value, "omega_tilt_error": err}


def _branch_payloads(*, omega_tilt: float, omega_tilt_error: float,
                     w2_upper: float, w2_branch_id: str) -> dict[str, Any]:
    """DL1 signed-curvature branch reports at a PARAMETERIZED W^2 ceiling
    (the v1 card hardcodes the registered ceiling; this generalization is the
    whole point of the v9 card)."""
    sigma2_error = SIGMA2_PLUGIN_ERROR_FRACTION * SIGMA2_PLUGIN_VALUE
    response = np.zeros((4, 4), dtype=float)
    response[0, 0] = 1.0 / sigma2_error
    response[1, 2] = 1.0 / omega_tilt_error
    g_hat = np.array([SIGMA2_PLUGIN_VALUE, 0.0, omega_tilt, 0.0], dtype=float)
    y = response @ g_hat
    c = np.array([1.0, -1.0, 1.0, 1.0], dtype=float)
    lower = np.zeros(4, dtype=float)
    upper = np.array([np.inf, float(w2_upper), np.inf, OMEGA_K_PLUGIN_UPPER],
                     dtype=float)
    input_modes = (
        ("Sigma2", "PLUGIN/BLOCKED"),
        ("W2_upper", w2_branch_id),
        ("Omega_tilt", "REAL_CF4_PLUS_DECLARED_OMEGA_M"),
        ("Omega_k_upper", "PLUGIN/BLOCKED"),
    )
    reports = signed_curvature_branch_reports(
        y, response, c, lower, upper, alpha1=0.05, alpha2=0.05,
        input_modes=input_modes, observational_claim_allowed=False)
    rows: dict[str, Any] = {}
    endpoint_se = math.sqrt(sigma2_error ** 2 + omega_tilt_error ** 2)
    for branch_id, report in reports.items():
        im_lo, im_hi, cn = im_interval(report.x_lo, report.x_hi,
                                       endpoint_se, endpoint_se)
        rows[branch_id] = {
            "status": report.status.upper(),
            "interval": [float(report.x_lo), float(report.x_hi)],
            "null_extremes": [float(report.null_lo), float(report.null_hi)],
            "im_95_ci": [float(im_lo), float(im_hi)],
            "im_c_n": float(cn),
        }
    return rows


def build_payload(*, generating_command: str) -> dict[str, Any]:
    for path in (FROZEN_V7_CARD, FROZEN_V8_CARD, K5_COVERAGE, OBS_DEFAULTS):
        if not path.is_file():
            raise FileNotFoundError(f"required artifact missing: {path}")
    k5 = json.loads(K5_COVERAGE.read_text())
    obs = json.loads(OBS_DEFAULTS.read_text())
    v8_card = json.loads(FROZEN_V8_CARD.read_text())

    bulk = k5["measured_bulk"]
    omega_m = float(obs["Omega_m"])
    tilt = _omega_tilt_from_bulk(
        bulk_amp_kms=float(bulk["amplitude_kms"]),
        bulk_err_kms=float(bulk["amplitude_error_kms"]),
        omega_m=omega_m)

    ceilings = w2_ceiling_branches()
    w2_branches: dict[str, Any] = {}
    for key, mode in (("registered", "REGISTERED_MES_CEILING_UNVERIFIED_"
                                     "NON_GEODESIC_PROVENANCE"),
                      ("hybrid_literature", "COMPARISON_ONLY_HYBRID_GEODESIC_"
                                            "COEFFS_X_FULL_OBSERVER_DIPOLE"),
                      ("sag_consistent", "COMPARISON_ONLY_GEODESIC_UNDER_"
                                         "SAG_EPS1_ZERO")):
        info = ceilings[key]
        w2_branches[f"W2_{key}"] = {
            "w2_upper": info["value_float"],
            "w2_upper_exact": info["value_exact"],
            "coefficients": info["coefficients"],
            "input_mode": mode,
            "curvature_branches": _branch_payloads(
                omega_tilt=tilt["omega_tilt"],
                omega_tilt_error=max(tilt["omega_tilt_error"], 1e-15),
                w2_upper=info["value_float"],
                w2_branch_id=mode),
        }

    inputs = (FROZEN_V7_CARD, FROZEN_V8_CARD, K5_COVERAGE, OBS_DEFAULTS)
    hashes = [f"{p.relative_to(REPO_ROOT).as_posix()}:sha256:{_sha(p)}"
              for p in inputs]
    config_hash = "sha256:" + hashlib.sha256(json.dumps({
        "inputs": hashes,
        "plugin_placeholders": {
            "Sigma2": SIGMA2_PLUGIN_VALUE,
            "Sigma2_error_fraction": SIGMA2_PLUGIN_ERROR_FRACTION,
            "Omega_k_upper": OMEGA_K_PLUGIN_UPPER,
        },
        "w2_ceilings": {k: v["value_float"] for k, v in ceilings.items()
                        if isinstance(v, dict) and "value_float" in v},
        "version": "v9-k5-identified-interval-card",
    }, sort_keys=True, default=float).encode()).hexdigest()

    payload: dict[str, Any] = {
        "artifact_id": "obsstat.k5_cf4_identified_interval_card_v9",
        "config_hash": config_hash,
        "input_hashes": hashes,
        "artifact_path": "docs/generated/k5_cf4_identified_interval_card_v9.json",
        "schema": "htt.k5.cf4_identified_interval_card.v2",
        "schema_version": "htt.k5.cf4_identified_interval_card.v2",
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
        "based_on_frozen_cards": {
            "v7": {"path": "docs/generated/k5_cf4_identified_interval_card.json",
                   "sha256": _sha(FROZEN_V7_CARD)},
            "v8": {"path": "docs/generated/k5_cf4_identified_interval_card_v8.json",
                   "sha256": _sha(FROZEN_V8_CARD)},
            "note": "both byte-frozen; the v8 Teff fingerprint row and "
                    "Omega_k documented-null status are inherited by "
                    "reference, not recomputed",
        },
        "bulk_flow_input": {
            "amplitude_kms": float(bulk["amplitude_kms"]),
            "amplitude_error_kms": float(bulk["amplitude_error_kms"]),
            "beta": tilt["beta"],
            "omega_tilt": tilt["omega_tilt"],
            "omega_tilt_error": tilt["omega_tilt_error"],
            "omega_m_declared": omega_m,
            "error_policy": "measurement_only (the cosmic-variance-inclusive "
                            "policy lives in the frozen v7 card rows)",
        },
        "eps1_attribution": eps1_attribution_triple(),
        "w2_ceiling_branches": w2_branches,
        "branch_reading": {
            "lower_endpoint_rule": "c_W = -1, so each W^2 ceiling fixes the "
                                   "LOWER interval endpoint at -U_W (plus "
                                   "the curvature-branch term)",
            "spread_quantifies": "how much the identified interval is keyed "
                                 "to the eps1 attribution choice; the "
                                 "registered branch stays the frozen anchor "
                                 "and NO branch is promoted",
            "v8_teff_fingerprint_row": "inherited by reference from the "
                                       "frozen v8 card",
            "omega_k_status": "inherited by reference from the frozen v8 "
                              "card (PLUGIN/BLOCKED + documented external-"
                              "prior null)",
        },
        "component_input_modes": {
            **dict(v8_card.get("component_input_modes", {})),
            "W2_upper": "THREE_LABELED_ATTRIBUTION_CONDITIONAL_BRANCHES "
                        "(registered / hybrid_literature / sag_consistent; "
                        "mes_branch_registry_seal)",
        },
        "caveats": [
            "Diagnostic pipeline-closure card only.",
            "All three W^2 ceilings are attribution-conditional; the "
            "registered value is the frozen anchor and none is promoted.",
            "The hybrid_literature ceiling mixes geodesic coefficients with "
            "the full observer dipole (NOT SAG's own eps1=0 convention).",
            "Sigma2 and Omega_k placeholders still block observational "
            "promotion.",
        ],
        "generating_command": generating_command,
        "git_commit_or_worktree_state": "content-addressed",
        "family_identification": False,
        "native_solver_result": False,
        "observational_claim_allowed": False,
    }
    return payload


def render_md(payload: dict[str, Any]) -> str:
    lines = [
        "# K5/CF4 identified-interval card v9 — three W^2 ceiling branches",
        "",
        f"Frozen bases: v7 `{payload['based_on_frozen_cards']['v7']['sha256'][:16]}...`, "
        f"v8 `{payload['based_on_frozen_cards']['v8']['sha256'][:16]}...`",
        "",
        "| W^2 branch | U_W | curvature branch | interval | IM 95% CI |",
        "| --- | --- | --- | --- | --- |",
    ]
    for wkey, wrow in payload["w2_ceiling_branches"].items():
        for bkey, brow in wrow["curvature_branches"].items():
            iv = brow["interval"]
            ci = brow["im_95_ci"]
            lines.append(
                f"| {wkey} | {wrow['w2_upper']:.4e} | {bkey} | "
                f"[{iv[0]:.6e}, {iv[1]:.6e}] | "
                f"[{ci[0]:.6e}, {ci[1]:.6e}] |")
    eps = payload["eps1_attribution"]
    lines += [
        "",
        f"eps1 attribution: observer_boost = conservative_total = "
        f"{eps['eps1_observer_boost']} (solar-beta rel diff "
        f"{eps['relative_difference_to_solar_beta']:.2e}); "
        f"cosmological = {eps['eps1_cosmological']} (SAG convention)",
        "",
        "No branch promoted; `observational_claim_allowed = False`.",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    check = "--check" in argv
    generating_command = f"venv/bin/python {SCRIPT_PATH}"
    payload = build_payload(generating_command=generating_command)

    issues = validate_manifest_payload(
        payload, manifest_path=OUT_JSON,
        expected_artifact_path="docs/generated/k5_cf4_identified_interval_card_v9.json")
    blocking = [i for i in issues if getattr(i, "severity", "error") == "error"]
    if blocking:
        for i in blocking:
            print(f"MANIFEST ISSUE: {i}", file=sys.stderr)
        return 1
    if payload["observational_claim_allowed"] is not False:
        print("FIREWALL VIOLATION: observational_claim_allowed must be False",
              file=sys.stderr)
        return 1

    js = json.dumps(payload, indent=2, sort_keys=True, default=float) + "\n"
    md = render_md(payload)
    if check:
        stale = [str(p) for p, text in ((OUT_JSON, js), (OUT_MD, md))
                 if not p.exists() or p.read_text() != text]
        if stale:
            print("stale v9 card artifacts:\n  " + "\n  ".join(stale),
                  file=sys.stderr)
            return 1
        print("v9 card artifacts current")
        return 0
    OUT_JSON.write_text(js)
    OUT_MD.write_text(md)
    print(f"wrote {OUT_JSON}\nwrote {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
