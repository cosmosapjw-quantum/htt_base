#!/usr/bin/env python3
"""Exact conditional slice examples and orbit diagnostics; no sky type labels.

Fixtures use the existing BASS geometric-unit interface: H and sigma have
inverse-length units, beta=v/c, and kappa=1 in these dimensionless numerical
examples. Physical c restoration is given in the accompanying theory note.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np


def clean(x):
    if isinstance(x, dict):
        return {k: clean(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [clean(v) for v in x]
    if isinstance(x, np.ndarray):
        return clean(x.tolist())
    if isinstance(x, (np.integer, np.bool_)):
        return x.item()
    if isinstance(x, (float, np.floating)):
        if not np.isfinite(x):
            raise ValueError("nonfinite scientific output")
        return float(x)
    return x


def run(root, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    if output.exists():
        raise ValueError("refusing to overwrite Bianchi examples")
    output.parent.mkdir(parents=True, exist_ok=True)
    sys.path[:0] = [str(root / "htt"), str(root / "htt/src")]
    from bass.background.bianchi_types import build_bianchi_algebra
    from bass.background.convention_bridge import build_structure_tensor_with_sign, exact_spatial_ricci_from_compact, exact_momentum_divergence
    from bass.background.tilted_bianchi_state import SpeciesFluidCongruence, construct_admissible_tilted_state, momentum_constraint_map
    from bass.diagnostics.bianchi_similarity import classify_bianchi_type, tilt_orbit_fingerprint

    def algebra(family, a, n):
        a, n = np.asarray(a, dtype=float), np.asarray(n, dtype=float)
        return replace(build_bianchi_algebra(family), a=a, n=n, C=build_structure_tensor_with_sign(a, n))

    def dust(q, rho):
        beta = np.asarray(q) / rho
        if rho <= 0 or beta @ beta >= 1:
            raise ValueError("nonphysical source")
        return SpeciesFluidCongruence(species="cdm", eps_hat=rho*(1-beta@beta), p_hat=0., v_vec=beta)

    def state_record(family, alg, sigma, rho, q):
        source = dust(q, rho)
        state = construct_admissible_tilted_state(family=family, algebra=alg, H=1., closure="hold_H", sigma_ab=sigma, species=[source])
        ric, scalar, _ = exact_spatial_ricci_from_compact(alg.a, alg.n)
        mp = momentum_constraint_map(alg)
        if not state.constraints.is_admissible:
            raise ValueError("constructed state failed its constraints")
        return dict(family=family, actual_class=classify_bianchi_type(alg.a, alg.n).label,
                    a=alg.a, n=alg.n, H=state.H, sigma=sigma, normal_rho=rho,
                    rest_energy_density=source.eps_hat, beta=source.v_vec, total_q=state.total_matter.q,
                    ricci=ric, ricci_scalar=scalar, ricci_stf=ric-scalar*np.eye(3)/3,
                    momentum_rank=mp.rank, momentum_singular_values=mp.singular_values,
                    momentum_matrix=mp.matrix, range_projector=mp.range_projector,
                    constraint_admissible=True, gauss_residual=state.constraints.hamiltonian_residual,
                    codazzi_residual=state.constraints.codazzi_residual_norm)

    s = .1
    ix_alg = algebra("IX", [0, 0, 0], np.diag([1., 2., 3.]))
    ix_sigma = np.array([[0., s, 0.], [s, 0., 0.], [0., 0., 0.]])
    ix = state_record("IX", ix_alg, ix_sigma, 5-s*s, [0., 0., -s])
    same_sigma = np.diag([.2, .1, -.3])
    class_a = {}
    for family in ("I", "II", "VI_0", "VII_0", "VIII", "IX"):
        alg = build_bianchi_algebra(family)
        _, scalar, _ = exact_spatial_ricci_from_compact(alg.a, alg.n)
        # Independent Hamiltonian rearrangement at H=1 and kappa=1.
        rho = 3. + .5*scalar - .5*np.sum(same_sigma**2)
        class_a[family] = state_record(family, alg, same_sigma, rho, np.zeros(3))

    v_alg = algebra("V", [.4, 0, 0], np.zeros((3, 3)))
    v_sigma = np.diag([0., .2, -.2])
    _, v_scalar, _ = exact_spatial_ricci_from_compact(v_alg.a, v_alg.n)
    v_rho = 3. + .5*v_scalar - .5*np.sum(v_sigma**2)
    type_v = state_record("V", v_alg, v_sigma, v_rho, np.zeros(3))
    type_v["momentum_kernel_norm"] = float(np.linalg.norm(v_sigma @ v_alg.a))
    type_v["det_sigma"] = float(np.linalg.det(v_sigma))

    ranks = []
    for h in (-.12, -1./9., -.10):
        # n2*n3=1/h for a=1; the h=-1/9 point is exceptional.
        alg = algebra("VI_h", [1., 0, 0], np.diag([0., 3., 1./(3*h)]))
        mp = momentum_constraint_map(alg)
        ranks.append(dict(h=h, numerical_rank=mp.rank, singular_values=mp.singular_values,
                          threshold=mp.rank_threshold, range_projector=mp.range_projector))
    if [x["numerical_rank"] for x in ranks] != [3, 2, 3]:
        raise ValueError("exceptional VI_h rank stratum failed")

    pairs = []
    flat_i = algebra("I", [0, 0, 0], np.zeros((3, 3)))
    flat_vii = algebra("VII_0", [0, 0, 0], np.diag([0., 1., 1.]))
    open_vii = algebra("VII_h", [.4, 0, 0], np.diag([0., 1., 1.]))
    for names, first, second in ((["I", "VII_0"], flat_i, flat_vii), (["V", "VII_h"], v_alg, open_vii)):
        ric1, _, _ = exact_spatial_ricci_from_compact(first.a, first.n)
        ric2, _, _ = exact_spatial_ricci_from_compact(second.a, second.n)
        mismatch = float(np.max(np.abs(ric1-ric2)))
        if mismatch > 1e-13:
            raise ValueError("intrinsic curvature example failed")
        pairs.append(dict(action_labels=names, ricci=ric1, ricci_max_difference=mismatch,
                          scope="Known constant-curvature intrinsic action degeneracy; extrinsic curvature/source/evolution not identified by this example"))

    jacobians = []
    for beta in ([0., 0, 0], [.2, 0, 0], [.2, .1, 0], [.2, .1, .3]):
        fp = tilt_orbit_fingerprint(np.zeros(3), np.diag([1., 2., 3.]), beta)
        jacobians.append(dict(beta=beta, squared_component_moment_rank=fp.moment_rank,
                              actual_velocity_jacobian_rank=fp.moment_jacobian_rank,
                              stabilizer_orbit_dimension=fp.stabilizer_orbit_dimension))
    result = dict(schema="htt.r62.bianchi_examples/1", status="IMPLEMENTATION_VERIFIED_CONDITIONAL_SLICE_CONSTRUCTIONS",
                  IX_tilt_counterexample=ix, same_H_and_sigma_class_A=class_a,
                  same_kinematics_scope="H and sigma coincide; source density is separately supplied for each curvature, so this is not equality of all observables or a universal no-go",
                  untilted_V=type_v, exceptional_VI_h_rank=ranks, constant_curvature_action_pairs=pairs,
                  tilt_moment_jacobians=jacobians,
                  limitations=["No observed Bianchi family posterior", "No ODE evolution or Boltzmann solver", "Geometric-unit fixtures; c-restoration specified in THEORY.md"],
                  script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    output.write_text(json.dumps(clean(result), indent=2)+"\n")
    print(json.dumps({"IX_beta": ix["beta"].tolist(), "IX_gauss": ix["gauss_residual"], "IX_codazzi": ix["codazzi_residual"],
                      "same_H_sigma_families": list(class_a), "VI_h_ranks": [x["numerical_rank"] for x in ranks]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run(args.root, args.output)
