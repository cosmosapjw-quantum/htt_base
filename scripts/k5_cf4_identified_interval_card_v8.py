#!/usr/bin/env python3
"""K5/CF4 identified-interval card, v8-update extension (NEW artifact).

The v7 card ``docs/generated/k5_cf4_identified_interval_card.json`` is
byte-frozen (embedded in the v7 report), so the v8-update additions land in a
NEW artifact pair ``k5_cf4_identified_interval_card_v8.{json,md}``:

* the FROZEN v7 card is carried by reference (path + SHA256) and its
  identified-interval payload is reproduced verbatim;
* NEW Teff fingerprint row: the SAME CF4 bulk-flow rapidity that drives the
  card's Omega_tilt also fixes the two-temperature mixing s = tanh(beta)
  (unification seal egs3.teff_unification), giving DETERMINISTIC fingerprint
  values (3/2) s^2 and (5/2) s^2 with the exact MES-dipole ceilings -- carried
  as derived quantities, never as measurements;
* NEW registered-external, Bianchi-VII_h-MODEL-CONDITIONAL vorticity/shear
  cross-check priors (Saadeh et al. 2016; Planck 2015 XVIII), which do NOT
  replace the MES W2_max registry and enable NO observational claim;
* the Omega_k component STAYS PLUGIN/BLOCKED, now with the documented
  external-prior NULL (no published Omega_k^aniso upper limit exists; survey
  docs/research_program/egs3/external_anisotropic_curvature_prior_survey.md);
* MES-coefficient provenance upgraded to the v8 state (sigma rederived
  bit-exact from the archived primary source; omega/accel primary-sourced).

``observational_claim_allowed`` stays False; the plugin firewall is intact.
``--check`` regenerates in memory and diffs against disk.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
for p in (REPO_ROOT, REPO_ROOT / "htt", REPO_ROOT / "htt/htt",
          REPO_ROOT / "htt/src"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

FROZEN_CARD = REPO_ROOT / "docs/generated/k5_cf4_identified_interval_card.json"
OUT_JSON = REPO_ROOT / "docs/generated/k5_cf4_identified_interval_card_v8.json"
OUT_MD = REPO_ROOT / "docs/generated/k5_cf4_identified_interval_card_v8.md"
SURVEY = "docs/research_program/egs3/external_anisotropic_curvature_prior_survey.md"
SCRIPT_PATH = "scripts/k5_cf4_identified_interval_card_v8.py"


def build_payload() -> dict:
    from htt.obsstat.egs3_teff_unification import (
        BETA_CF4, fingerprint_ceilings)

    frozen = json.loads(FROZEN_CARD.read_text())
    frozen_sha = hashlib.sha256(FROZEN_CARD.read_bytes()).hexdigest()

    ceil = fingerprint_ceilings()
    cf4 = ceil["cf4_containment"]
    teff_row = {
        "driver": "the CF4 bulk-flow rapidity that also drives the card's "
                  "Omega_tilt (seal egs3.teff_unification; the unification "
                  "module's |B| = 340.7264 km/s is the card value rounded at "
                  "1e-7 relative -- disclosed)",
        "beta_cf4_rapidity": cf4["beta_cf4"],
        "s_mixing_tanh_beta": cf4["s_cf4_tanh"],
        "fingerprint_R3_deviation_3half_s2": cf4["fingerprint_3half_s2"],
        "fingerprint_R5_deviation_5half_s2": 2.5 * cf4["s_cf4_tanh"] ** 2,
        "mes_dipole_ceiling_R3": ceil["ceiling_R3_float"],
        "mes_dipole_ceiling_R5": ceil["ceiling_R5_float"],
        "mes_dipole_ceiling_R3_exact": ceil["ceiling_R3_exact"],
        "mes_dipole_ceiling_R5_exact": ceil["ceiling_R5_exact"],
        "fingerprint_below_ceiling": cf4["fingerprint_below_ceiling"],
        "containment_is_trivial_inequality": "reduces to s_CF4 < eps1 (the CF4 bulk-flow rapidity below the CMB-dipole amplitude); a consistency disclosure, NOT a null-test result",
        "input_mode": "DERIVED_FROM_UNIFICATION_SEAL_DETERMINISTIC",
        "not_a_measurement": True,
        "statistical_lane": "coverage/calibration run at DISPLAY mixings only "
                            "(seal egs3.teff_statistical); CF4-scale sampling "
                            "would be pure noise -- disclosed",
    }

    external_priors = {
        "applicability": "Bianchi-VII_h-MODEL-CONDITIONAL published limits; "
                         "cross-checks only -- they do NOT replace the MES "
                         "W2_max registry and enable NO observational claim",
        "vorticity_omega_over_H": [
            {"limit_95": 5.2e-11, "source": "Saadeh et al., PRL 117, 131302 "
             "(2016), arXiv:1605.07178 -- the paper's own vorticity recast of "
             "its vector-mode shear limit (sigma_V/H)_0 < 4.7e-11; the two "
             "numbers are DISTINCT quantities from one source"},
            {"limit_95": 7.6e-10, "source": "Planck 2015 XVIII, A&A 594, A18, "
             "arXiv:1502.01593 (open-coupled VII_h, T)"},
        ],
        "shear_sigma_over_H_weakest_mode": {
            "limit_95": 1.0e-6, "mode": "regular tensor",
            "source": "Saadeh et al. 2016, Table II (Planck, all-mode)"},
    }

    omega_k_block = {
        "input_mode": "PLUGIN/BLOCKED (unchanged)",
        "leading_order_structural_null": "certified (measured_response_seal); "
                                         "leading-EGS-order no-channel",
        "external_prior_branch": "DOCUMENTED NULL -- no published direct "
                                 "Omega_k^aniso upper limit exists; Bianchi "
                                 "VII_h analyses marginalize Omega_K as a "
                                 "prior; fabricating a ceiling is forbidden",
        "survey": SURVEY,
        "higher_order_transfer_branch": "open (ticket "
                                        "k5_omega_k_higher_order_ceiling)",
    }

    modes = dict(frozen["component_input_modes"])
    modes["MES_coefficients"] = ("SIGMA_REDERIVED_BIT_EXACT_FROM_PRIMARY_"
                                 "SOURCE; OMEGA_ACCEL_PRIMARY_SOURCED_NOT_"
                                 "REDERIVABLE (mes_rederivation_seal, v8)")
    modes["Teff_fingerprint"] = "DERIVED_FROM_UNIFICATION_SEAL_DETERMINISTIC"
    modes["External_vorticity_shear_priors"] = ("REGISTERED_EXTERNAL_MODEL_"
                                                "CONDITIONAL_CROSSCHECK_ONLY")

    payload = dict(frozen)
    payload.update({
        "artifact_id": "k5_cf4_identified_interval_card_v8",
        "artifact_path": "docs/generated/k5_cf4_identified_interval_card_v8.json",
        "generating_command": f"venv/bin/python {SCRIPT_PATH}",
        "schema": "htt.k5_cf4_identified_interval_card.v8",
        "based_on_frozen_v7_card": {
            "path": "docs/generated/k5_cf4_identified_interval_card.json",
            "sha256": frozen_sha,
            "note": "v7 card byte-frozen (embedded in the v7 report); its "
                    "interval payload is inherited verbatim above",
        },
        "component_input_modes": modes,
        "v8_teff_fingerprint_row": teff_row,
        "v8_external_model_conditional_priors": external_priors,
        "v8_omega_k_status": omega_k_block,
        "observational_claim_allowed": False,
    })
    caveats = list(payload.get("caveats", []))
    caveats.append("v8 additions are derived/registered-external rows only; "
                   "no component was promoted to a measurement; the plugin "
                   "firewall and observational_claim_allowed=False are "
                   "unchanged")
    payload["caveats"] = caveats
    return payload


def render_md(payload: dict) -> str:
    t = payload["v8_teff_fingerprint_row"]
    ok = payload["v8_omega_k_status"]
    lines = [
        "# K5/CF4 identified-interval card -- v8-update extension",
        "",
        f"Frozen v7 base: `{payload['based_on_frozen_v7_card']['path']}` "
        f"(sha256 `{payload['based_on_frozen_v7_card']['sha256'][:16]}...`)",
        "",
        "## Teff fingerprint row (deterministic, one boost -> two channels)",
        "",
        "| quantity | value |",
        "| --- | --- |",
        f"| beta_CF4 (rapidity) | {t['beta_cf4_rapidity']:.9e} |",
        f"| s = tanh(beta) | {t['s_mixing_tanh_beta']:.9e} |",
        f"| (3/2) s^2 (R3 deviation) | {t['fingerprint_R3_deviation_3half_s2']:.6e} |",
        f"| (5/2) s^2 (R5 deviation) | {t['fingerprint_R5_deviation_5half_s2']:.6e} |",
        f"| MES dipole ceiling R3 | {t['mes_dipole_ceiling_R3']:.6e} "
        f"(= {t['mes_dipole_ceiling_R3_exact']}) |",
        f"| MES dipole ceiling R5 | {t['mes_dipole_ceiling_R5']:.6e} "
        f"(= {t['mes_dipole_ceiling_R5_exact']}) |",
        f"| fingerprint below ceiling | {t['fingerprint_below_ceiling']} |",
        "",
        "NOT a measurement; derived from the unification seal. Statistical "
        "coverage/calibration ran at display mixings only "
        "(egs3.teff_statistical).",
        "",
        "## Omega_k status",
        "",
        f"- {ok['input_mode']}; {ok['leading_order_structural_null']}",
        f"- external-prior branch: {ok['external_prior_branch']}",
        f"- survey: `{ok['survey']}`",
        "",
        "## Registered-external model-conditional cross-checks",
        "",
        "(omega/H)_0 < 5.2e-11 (Saadeh 2016) / < 7.6e-10 (Planck 2015 XVIII); "
        "(sigma_T,reg/H)_0 < 1.0e-6 (Saadeh 2016). Bianchi-VII_h-conditional; "
        "cross-checks only; no observational claim enabled.",
        "",
        f"`observational_claim_allowed = {payload['observational_claim_allowed']}`",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    check = "--check" in argv
    payload = build_payload()

    from common.artifact_manifest import validate_manifest_payload
    issues = validate_manifest_payload(
        payload, manifest_path=OUT_JSON,
        expected_artifact_path="docs/generated/k5_cf4_identified_interval_card_v8.json")
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
            print("stale v8 card artifacts:\n  " + "\n  ".join(stale),
                  file=sys.stderr)
            return 1
        print("v8 card artifacts current")
        return 0
    OUT_JSON.write_text(js)
    OUT_MD.write_text(md)
    print(f"wrote {OUT_JSON}\nwrote {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
