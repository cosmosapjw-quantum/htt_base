#!/usr/bin/env python3
"""Run the EGS2-extension experiments (NT2-A1/A2/B1/B2/B3) + blocker discharges
against the canonical repo modules and write docs/generated/egs2_experiments.json.

All outputs are conditional-theorem / synthetic-mechanics evidence. They are NOT
a detection, a Bianchi-family/geometry claim, or native solver validation. The
toy Fisher response and the scalarized shear hierarchy are documented constructs;
the analytic *shapes* (floor < 0.632, exclusion of zero, sourced transport, joint
blind sector) are robust, the exact numbers need the covariant coefficients and
real low-l data (semi-native calculator ticket).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "docs/generated/egs2_experiments.json"


def nt2_a1_a2() -> dict:
    from htt.obsstat.egs2_fisher import (
        fisher_floor, single_ell_sampling_dispersion, mc_estimator_dispersion,
        octupole_sufficiency_tail)
    floors = {f"L{L}_fsky{fs}": fisher_floor(L, fs)
              for L in (2, 3, 5, 10, 20) for fs in (1.0, 0.7)}
    mc = {f"L{L}": vars(mc_estimator_dispersion(L, 1.0, n_real=4000, seed=21)) for L in (2, 5, 10)}
    return {
        "theorem": "NT2-A1 (genuine multi-multipole Fisher-CR floor) + NT2-A2 (octupole saturation)",
        "single_ell_dispersion_l2": single_ell_sampling_dispersion(2, 1.0),
        "fisher_floor": floors,
        "mc_mle_vs_floor": mc,
        "octupole_tail_l80": octupole_sufficiency_tail(80, 1.0),
        "headline": "floor 0.632(L=2)->0.474(L=5)->0.424(L=20); MC MLE ratio ~1; strictly below single-l 0.632",
    }


def nt2_b1() -> dict:
    from htt.obsstat.egs2_shear_bracket import filling_bracket
    rows = []
    for a2, a3 in [(1e-5, 2e-6), (1e-5, 5e-6), (3e-5, 6e-6), (1e-4, 3e-5)]:
        br = filling_bracket(a2, a3)
        rows.append(vars(br))
    return {"theorem": "NT2-B1 (two-sided shear/F bracket; zero excluded under H3)",
            "rows": rows,
            "headline": "a nonzero quadrupole forbids a vanishing shear-filling (F_lo>0 under H3)"}


def nt2_b2() -> dict:
    from htt.obsstat.egs2_transport import sourced_depth_transport
    r = sourced_depth_transport()
    return {"theorem": "NT2-B2 (GR shear-memory-sourced depth transport of G_F)",
            **vars(r),
            "headline": "steady tilt stress -> flat G_F; growing Pi(z) -> depth-evolving G_F (GR-sourced)"}


def nt2_b3() -> dict:
    from htt.obsstat.egs2_transport import vorticity_blind_sector
    b = vorticity_blind_sector(n_configs=1000, seed=33)
    return {"theorem": "NT2-B3 (vorticity joint blind sector: CMB-T + radial velocity)",
            **vars(b),
            "headline": "no estimator on CMB-T + radial velocities alone constrains the comparator's W^2 term"}


def block_k1() -> dict:
    from htt.obsstat.lowell_global_calibration import e2e_maxscan_from_summaries
    rng = np.random.default_rng(1234)
    e2e = rng.normal(size=(300, 6))
    observed = rng.normal(size=6); observed[1] = 3.5
    directions = ["high"] + ["two-sided"] * 5
    out = e2e_maxscan_from_summaries(observed, e2e, directions)
    out["note"] = "synthetic E2E stand-in; swap for healpy reads of the public PLA FFP10/NPIPE maps"
    return out


def block_k6() -> dict:
    from htt.obsstat.constrained_realizations import curl_posterior
    p = curl_posterior(signal_var=1.0, noise_var=0.5, n_cr=400, seed=4242)
    return {"discharge": "BLOCK-K6 Hoffman-Ribak constrained-realization curl posterior",
            **vars(p),
            "note": "toy 1D curl sector; swap for the 3D CF4 WF/CR ensemble (still BLOCKED_MISSING_FIELD_REALIZATIONS)",
            "blocker_until_real_field": "BLOCKED_MISSING_FIELD_REALIZATIONS"}


def main() -> int:
    payload = {
        "schema": "htt.egs2.experiments.v1",
        "claim_tier": "program_theorem_and_synthetic_mechanics",
        "family_identification": False,
        "native_solver_result": False,
        "experiments": {
            "NT2_A1_A2_fisher_floor": nt2_a1_a2(),
            "NT2_B1_two_sided_bracket": nt2_b1(),
            "NT2_B2_sourced_transport": nt2_b2(),
            "NT2_B3_blind_sector": nt2_b3(),
            "BLOCK_K1_e2e_maxscan": block_k1(),
            "BLOCK_K6_hoffman_ribak": block_k6(),
        },
        "blockers_kept_open": [
            "BLOCKED_MISSING_PR4_E2E_ACCESS",
            "BLOCKED_MISSING_RELEASE_MOCK_OWNERSHIP",
            "BLOCKED_MISSING_FIELD_REALIZATIONS",
            "AWAITING_NATIVE_LOWELL_SOLVER",
        ],
        "claim_boundary": "conditional EGS-type theorems + synthetic mechanics only; no detection, no family/geometry, no native solver validation",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, default=float) + "\n")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
