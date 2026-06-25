#!/usr/bin/env python3
"""Run the PR07/PR08 synthetic + theorem experiments against the canonical
repo modules and write evidence JSON under docs/generated/.

All outputs are synthetic/structural mechanics. They are NOT new observational
measurements: no family identification, global tilt, or physical-vorticity
detection is produced.
"""
from __future__ import annotations

import json
from pathlib import Path
import numpy as np

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "docs/generated"


def paper_a() -> dict:
    from htt.departure.paper_a_closure import (
        numerical_rank, duplicate_block_audit, radial_vorticity_response,
        single_shell_dipole_design, temporal_tensor_design,
        boost_composition_audit, first_jet_counterexample)
    rng = np.random.default_rng(11)
    A = rng.normal(size=(9, 4))
    directions = rng.normal(size=(300, 3))
    radii = rng.uniform(10, 200, size=300)
    shell = single_shell_dipole_design(directions, np.full(300, 80.0))
    broad = single_shell_dipole_design(directions, np.exp(rng.uniform(np.log(20), np.log(220), size=300)))
    T = np.array([[1., 0., 0.], [0.4, 1., 0.], [0.2, 0.5, 1.]])
    return {
        "duplicate": duplicate_block_audit(A),
        "radial_vorticity_max_abs": float(np.max(np.abs(radial_vorticity_response(directions, radii)))),
        "single_shell_rank": numerical_rank(shell),
        "broad_depth_rank": numerical_rank(broad),
        "temporal_tensor_rank": numerical_rank(temporal_tensor_design(T)),
        "boost": boost_composition_audit(np.array([0.2, 0, 0]), np.array([0, 0.15, 0])),
        "first_jet": first_jet_counterexample(0.2),
        "claim_tier": "program_theorem_synthetic",
    }


def paper_b() -> dict:
    from bass.background.bi_continuation import SpeciesPrimitive, BIState, dust_flrw_exact
    from bass.background.bi_continuation.moments import total_projection
    from bass.background.bi_continuation.verification import (
        random_species_audit, constraint_transport_residual, integrate_solve_ivp)
    random_audit = random_species_audit(samples=1000, seed=20260625)
    pair = (SpeciesPrimitive(0.55, 0.0, np.array([0.18, 0, 0])),
            SpeciesPrimitive(0.55, 0.0, np.array([-0.18, 0, 0])))
    sigma = np.diag([0.03, -0.012, -0.018])
    p = total_projection(pair)
    sigma2 = 0.5 * np.sum(sigma * sigma)
    H = np.sqrt((p.mu + sigma2) / 3.0)
    state = BIState(1.0, H, sigma, pair)
    transport = constraint_transport_residual(state)
    H0 = 0.8
    t = np.linspace(0, 0.4, 101)
    dust = BIState(1.0, H0, np.zeros((3, 3)), (SpeciesPrimitive(3 * H0 * H0, 0.0, np.zeros(3)),))
    ae, He = dust_flrw_exact(t, H0)
    integrators = {}
    for method in ("DOP853", "Radau"):
        hist = integrate_solve_ivp(dust, t, method=method, rtol=1e-11, atol=1e-13)
        integrators[method] = {
            "max_a_abs_error": float(max(abs(s.a - a) for s, a in zip(hist, ae))),
            "max_H_abs_error": float(max(abs(s.H - h) for s, h in zip(hist, He))),
        }
    return {
        "random_conservation": random_audit,
        "constraint_transport": {
            "gauss": float(transport["gauss"]),
            "gauss_transport_residual": float(transport["gauss_transport_residual"]),
            "codazzi_norm": float(np.linalg.norm(p.flux)),
            "codazzi_transport_residual_norm": float(np.linalg.norm(transport["codazzi_transport_residual"])),
        },
        "integrator_crosscheck": integrators,
        "claim_tier": "program_theorem_synthetic",
    }


def k1() -> dict:
    from htt.obsstat.lowell_global_calibration import synthetic_correlated_scan
    return synthetic_correlated_scan()


def k5() -> dict:
    from htt.obsstat.bulkflow_mle import hierarchical_coverage_experiment
    return hierarchical_coverage_experiment(simulations=500)


def k6() -> dict:
    from htt.obsstat.affine_flow import curl_suppression_ensemble
    return curl_suppression_ensemble()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    products = {
        "pr07_paper_a.json": paper_a(),
        "pr07_paper_b.json": paper_b(),
        "pr07_k1_global_synthetic.json": k1(),
        "pr07_k5_hierarchical_synthetic.json": k5(),
        "pr07_k6_affine_ensemble_synthetic.json": k6(),
    }
    for name, payload in products.items():
        (OUT / name).write_text(json.dumps(payload, indent=2) + "\n")
        print(f"wrote {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
