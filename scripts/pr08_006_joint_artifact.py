#!/usr/bin/env python3
"""PR08-006: joint posterior artifact over the discharged sectors.

Assembles the real-data discharges (K1/K5/K6) into the graded comparator
g = (Sigma^2, W^2, Omega_tilt, Omega_k) of the EGS3 framework, with each sector
carrying its real status and provenance. Only identified components enter the
pushforward; missing/blind sectors are explicit and **fail closed** (never set to
zero). Data rank is reported separately from prior-conditioned rank. No MIO
certificate is consumed as posterior odds; no scalar is promoted to a family.

Sector map (per EGS3-A1 rank-2 identifiability, now on real data):
  Omega_tilt  <- K5  CF4 bulk flow            : MEASURED (reachable)
  Sigma^2     <- K1  low-l CMB quadrupole/morph: PARTIAL  (look-elsewhere only;
                                                 E2E-systematics null still blocked)
  W^2         <- K6  CF4 vorticity            : FAIL-CLOSED (structural no-go;
                                                 curl-suppressed WF reconstruction)
  Omega_k     <- (no channel)                 : FAIL-CLOSED (no low-l channel)

This realises the program headline --- a rank-2 graded comparator with ONE
measured kinematic sector (Omega_tilt), ONE partial CMB sector (Sigma^2), and TWO
fail-closed sectors (the two-sector no-go W^2, Omega_k) --- with actual numbers,
while keeping the blind sectors fail-closed. The rank-2 count is one full plus one
partial, not two fully measured sectors. Diagnostic-only; no Bianchi family,
geometry, anisotropy-evidence, or native-solver claim.

Outputs: docs/generated/pr08_006_joint_artifact.json. Deterministic; --check.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
for root in (REPO_ROOT / "htt", REPO_ROOT / "htt/htt", REPO_ROOT):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

from obsstat.egs3_graded_comparator import SECTORS, NULL_SECTOR_KIND  # noqa: E402

GEN = REPO_ROOT / "docs/generated"
OUT_JSON = GEN / "pr08_006_joint_artifact.json"


def _load(name: str) -> dict:
    p = GEN / name
    return json.loads(p.read_text()) if p.is_file() else {}


def build_report() -> dict:
    k1 = _load("k1_global_maxscan.json")
    k5 = _load("k5_cf4_release_coverage.json")
    k6 = _load("k6_cf4_curl_posterior.json")

    sectors = {
        "Omega_tilt": {
            "status": "measured",
            "source": "K5 CF4 bulk flow (real Tully+2023 release)",
            "value_kms": k5.get("measured_bulk", {}).get("amplitude_kms"),
            "error_kms": k5.get("coverage", {}).get("total_amplitude_error_kms"),
            "coverage_cv_inclusive": k5.get("coverage", {}).get("cosmic_variance_inclusive", {}).get("amplitude_coverage"),
            "coverage_is_conditional_on_lambdacdm_sigma_cv_prior": True,
            "blocker": None,
            "note": "bulk-flow amplitude is the reachable tilt/dipole sector (model-independent kinematic descriptor); consistent with the LambdaCDM ~150-250 km/s expectation. The CV-inclusive coverage is conditional on a fixed LambdaCDM sigma_cv=150 km/s/comp prior; full release-matched mocks remain BLOCKED_MISSING_RELEASE_MOCK_OWNERSHIP",
        },
        "Sigma2": {
            "status": "partial",
            "source": "K1 low-l CMB morphology (quadrupole-bearing)",
            "global_p_smica": k1.get("smica", {}).get("global_p"),
            "global_p_commander": k1.get("commander", {}).get("global_p"),
            "blocker": "BLOCKED_MISSING_PR4_E2E_ACCESS",
            "note": "look-elsewhere global p discharged under a LambdaCDM null; the E2E-systematics calibration is not bound, so the shear sector is only partially probed",
        },
        "W2": {
            "status": "fail_closed_structural_no_go",
            "source": "K6 CF4 WF mean-field vorticity",
            "vorticity_over_shear_max": k6.get("vorticity_over_shear_ratio_max"),
            "blocker": "BLOCKED_MISSING_FIELD_REALIZATIONS (WF mean-field no-go established; true CR posterior still blocked)",
            "note": "the CF4 WF mean-field reconstruction is curl-suppressed (WF prior, across modes); the vorticity sector is structurally unidentifiable from it (NOT set to zero). A true Hoffman-Ribak CR posterior remains blocked until a CR ensemble is owned",
            "null_kind": NULL_SECTOR_KIND["W2"]["kind"],
            "null_order_dependence": NULL_SECTOR_KIND["W2"]["order_dependence"],
            "reopens_via": list(NULL_SECTOR_KIND["W2"]["reopens_via"]),
        },
        "Omega_k": {
            "status": "fail_closed_no_channel",
            "source": None,
            "blocker": "no_low_ell_channel_sources_anisotropic_curvature",
            "note": "no registered low-l channel reaches the anisotropic-curvature sector at leading EGS order (NOT set to zero); re-opens beyond leading order, unlike W2",
            "null_kind": NULL_SECTOR_KIND["Omega_k"]["kind"],
            "null_order_dependence": NULL_SECTOR_KIND["Omega_k"]["order_dependence"],
            "reopens_via": list(NULL_SECTOR_KIND["Omega_k"]["reopens_via"]),
        },
    }

    measured = [s for s, v in sectors.items() if v["status"] == "measured"]
    partial = [s for s, v in sectors.items() if v["status"] == "partial"]
    fail_closed = [s for s, v in sectors.items() if v["status"].startswith("fail_closed")]

    return {
        "schema": "htt.pr08_006.joint_artifact.v1",
        "ticket": "PR08-006",
        "owner": "consensus_editor",
        "claim_tier": "diagnostic_only",
        "family_identification": False,
        "native_solver_result": False,
        "mio_as_odds": False,
        "scalar_to_family_promotion": False,
        "graded_sectors": list(SECTORS),
        "sectors": sectors,
        "data_rank": {
            "reachable_full": measured,
            "reachable_partial": partial,
            "data_rank_count": len(measured) + len(partial),
            "note": "data rank counts sectors with a real channel (K5 full + K1 partial); it is NOT prior-conditioned",
        },
        "prior_conditioned_rank": {
            "sectors": measured + partial,
            "count": len(measured) + len(partial),
            "note": "no prior is invoked to add a sector; prior-conditioned rank equals data rank here",
        },
        "two_sector_no_go": {
            "blind_sectors": fail_closed,
            "statement": "W^2 (vorticity) and Omega_k (anisotropic curvature) are both fail-closed, but they are NOT the same KIND of null. W^2 is a GENUINE, order-INDEPENDENT structural null (radial n.Omega.n=0 + CMB curl/Weyl-blind at EGS order); it re-opens only via a different observable (transverse velocities, B-modes). Omega_k is a LEADING-EGS-ORDER no-channel (no low-l channel sources anisotropic curvature at leading order); it is truncation-dependent and re-opens beyond leading order (higher-order ISW, lensing, native low-l transfer). Neither is set to zero.",
            "null_kinds": {s: NULL_SECTOR_KIND[s] for s in fail_closed if s in NULL_SECTOR_KIND},
        },
        "x_C_single_scalar": None,
        "x_C_withheld_reason": "x_C is NOT collapsed to a single number: two of the four sectors are fail-closed, so a scalar comparator would require setting blind sectors to zero (forbidden). The graded vector is reported per-sector instead.",
        "claim_boundary": "joint pushforward of identified sectors only; blind/partial sectors explicit and fail-closed; no MIO-as-odds, no scalar-to-family, no native-atlas/geometry claim",
        "caveats": [
            "Omega_tilt (K5) is a model-independent bulk-flow descriptor, not anisotropy evidence.",
            "Sigma^2 (K1) is partial: look-elsewhere only, E2E null still blocked.",
            "W^2 (K6) is a structural no-go from a curl-suppressed reconstruction, not a vorticity measurement.",
            "Omega_k has no channel and is fail-closed.",
            "No combined scalar x_C is reported because blind sectors must not be zeroed.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    payload = build_report()
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.check:
        if not OUT_JSON.is_file() or OUT_JSON.read_text() != text:
            print("stale pr08_006_joint_artifact.json; rerun scripts/pr08_006_joint_artifact.py")
            return 1
        print("pr08_006_joint_artifact.json up to date")
        return 0
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(text)
    print(f"wrote {OUT_JSON.relative_to(REPO_ROOT)}")
    print(f"   data rank {payload['data_rank']['data_rank_count']} "
          f"(measured {payload['data_rank']['reachable_full']}, partial {payload['data_rank']['reachable_partial']}); "
          f"fail-closed {payload['two_sector_no_go']['blind_sectors']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
